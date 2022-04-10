import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim
import numpy as np
torch.manual_seed(1)
from sklearn.metrics import roc_auc_score
from sklearn.metrics import f1_score
import copy

from timeit import default_timer as timer
from datetime import timedelta

##########################################################

start_program = timer()

label_to_ix=np.load('label_to_ix.npy').item()
ix_to_label=np.load('ix_to_label.npy')
training_data=np.load('training_data.npy')
test_data=np.load('test_data.npy')
val_data=np.load('val_data.npy')
word_to_ix=np.load('word_to_ix.npy').item()
ix_to_word=np.load('ix_to_word.npy')
newwikivec=np.load('newwikivec.npy')
wikivoc=np.load('wikivoc.npy').item()

wikisize=newwikivec.shape[0]
rvocsize=newwikivec.shape[1]
wikivec=autograd.Variable(torch.FloatTensor(newwikivec))


batchsize=32



def preprocessing(data):

    new_data=[]
    for i, note, j in data:
        templabel=[0.0]*len(label_to_ix)
        for jj in j:
            if jj in wikivoc:
                templabel[label_to_ix[jj]]=1.0
        templabel=np.array(templabel,dtype=float)
        new_data.append((i, note, templabel))
    new_data=np.array(new_data)
    
    lenlist=[]
    for i in new_data:
        lenlist.append(len(i[0]))
    sortlen=sorted(range(len(lenlist)), key=lambda k: lenlist[k])  
    new_data=new_data[sortlen]
    
    batch_data=[]
    
    for start_ix in range(0, len(new_data)-batchsize+1, batchsize):
        thisblock=new_data[start_ix:start_ix+batchsize]
        mybsize= len(thisblock)
        numword=np.max([len(ii[0]) for ii in thisblock])
        main_matrix = np.zeros((mybsize, numword), dtype= np.int)
        for i in range(main_matrix.shape[0]):
            for j in range(main_matrix.shape[1]):
                try:
                    if thisblock[i][0][j] in word_to_ix:
                        main_matrix[i,j] = word_to_ix[thisblock[i][0][j]]
                    
                except IndexError:
                    pass       # because initialze with 0, so you pad with 0
    
        xxx2=[]
        yyy=[]
        for ii in thisblock:
            xxx2.append(ii[1])
            yyy.append(ii[2])
        
        xxx2=np.array(xxx2)
        yyy=np.array(yyy)
        batch_data.append((autograd.Variable(torch.from_numpy(main_matrix)),autograd.Variable(torch.FloatTensor(xxx2)),autograd.Variable(torch.FloatTensor(yyy))))
    return batch_data
batchtraining_data=preprocessing(training_data)
batchtest_data=preprocessing(test_data)
batchval_data=preprocessing(val_data)


######################################################################
# Create the model:

Embeddingsize=100
hidden_dim=200
class LSTM(nn.Module):

    def __init__(self, batch_size, vocab_size, tagset_size):
        super(LSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.word_embeddings = nn.Embedding(vocab_size+1, Embeddingsize, padding_idx=0)
        self.lstm = nn.LSTM(Embeddingsize, hidden_dim, bidirectional=True)
        self.hidden2tag = nn.Linear(2*hidden_dim, tagset_size)
        self.hidden = self.init_hidden()
        
        
        self.layer2 = nn.Linear(Embeddingsize, 1,bias=False)
        self.embedding=nn.Linear(rvocsize,Embeddingsize)
        self.vattention=nn.Linear(Embeddingsize,Embeddingsize,bias=False)
        
        self.softmax = nn.Softmax()
        self.sigmoid = nn.Sigmoid()
        self.tanh = nn.Tanh()
        self.embed_drop = nn.Dropout(p=0.2)
    
    def init_hidden(self):
        return (autograd.Variable(torch.zeros(2, batchsize, self.hidden_dim).cuda()),
                autograd.Variable(torch.zeros(2, batchsize, self.hidden_dim)).cuda())

    
    def forward(self, vec1, nvec, wiki, simlearning):
      
        thisembeddings=self.word_embeddings(vec1).transpose(0,1)
        thisembeddings = self.embed_drop(thisembeddings)
       
        if simlearning==1:
            nvec=nvec.view(batchsize,1,-1)
            nvec=nvec.expand(batchsize,wiki.size()[0],-1)
            wiki=wiki.view(1,wiki.size()[0],-1)
            wiki=wiki.expand(nvec.size()[0],wiki.size()[1],-1)
            new=wiki*nvec
            new=self.embedding(new)
            vattention=self.sigmoid(self.vattention(new))
            new=new*vattention
            vec3=self.layer2(new)
            vec3=vec3.view(batchsize,-1)
        
        #print("EMB: ", thisembeddings.shape)
        #print("HIDDEN: ", self.hidden)

        lstm_out, self.hidden = self.lstm(
            thisembeddings, self.hidden)

        #print(lstm_out.shape)
        #print(self.hidden)
        
        lstm_out=lstm_out.transpose(0,2).transpose(0,1)
        
        output1=nn.MaxPool1d(lstm_out.size()[2])(lstm_out).view(batchsize,-1)
        
        vec2 = self.hidden2tag(output1)
        if simlearning==1:
            tag_scores = self.sigmoid(vec2.detach()+vec3)
        else:
            tag_scores = self.sigmoid(vec2)
        
        
        return tag_scores

######################################################################
# Train the model:

topk=10

def trainmodel(model, sim):
    print ('start_training')
    modelsaved=[]
    modelperform=[]
    topk=10
    
    
    bestresults=-1
    bestiter=-1
    for epoch in range(5000):  
        
        model.train()
        
        lossestrain = []
        recall=[]
        for mysentence in batchtraining_data:
            model.zero_grad()
            model.hidden = model.init_hidden()
            targets = mysentence[2].cuda()
            tag_scores = model(mysentence[0].cuda(),mysentence[1].cuda(),wikivec.cuda(),sim)
            loss = loss_function(tag_scores, targets)
            loss.backward()
            optimizer.step()
            lossestrain.append(loss.data.mean())
        print (epoch)
        
        modelsaved.append(copy.deepcopy(model.state_dict()))
        print ("XXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        model.eval()
    
        recall=[]
        for inputs in batchval_data:
            model.hidden = model.init_hidden()
            targets = inputs[2].cuda()
            tag_scores = model(inputs[0].cuda(),inputs[1].cuda() ,wikivec.cuda(),sim)
    
            loss = loss_function(tag_scores, targets)
            
            targets=targets.data.cpu().numpy()
            tag_scores= tag_scores.data.cpu().numpy()
            
            
            for iii in range(0,len(tag_scores)):
                temp={}
                for iiii in range(0,len(tag_scores[iii])):
                    temp[iiii]=tag_scores[iii][iiii]
                temp1=[(k, temp[k]) for k in sorted(temp, key=temp.get, reverse=True)]
                thistop=int(np.sum(targets[iii]))
                hit=0.0
                for ii in temp1[0:max(thistop,topk)]:
                    if targets[iii][ii[0]]==1.0:
                        hit=hit+1
                if thistop!=0:
                    recall.append(hit/thistop)
            
        print ('validation top-',topk, np.mean(recall))
        
        
        
        modelperform.append(np.mean(recall))
        if modelperform[-1]>bestresults:
            bestresults=modelperform[-1]
            bestiter=len(modelperform)-1
        
        if (len(modelperform)-bestiter)>5:
            print (modelperform,bestiter)
            return modelsaved[bestiter]
    
model = LSTM(batchsize, len(word_to_ix), len(label_to_ix))
model.cuda()

loss_function = nn.BCELoss()
optimizer = optim.Adam(model.parameters())

start_train0 = timer()
basemodel= trainmodel(model, 0)
torch.save(basemodel, 'LSTM_model')
end_train0 = timer()

model = LSTM(batchsize, len(word_to_ix), len(label_to_ix))
model.cuda()
model.load_state_dict(basemodel)
loss_function = nn.BCELoss()
optimizer = optim.Adam(model.parameters())

start_train1 = timer()
KSImodel= trainmodel(model, 1)
torch.save(KSImodel, 'KSI_LSTM_model')
end_train1 = timer()

def testmodel(modelstate, sim):
    model = LSTM(batchsize, len(word_to_ix), len(label_to_ix))
    model.cuda()
    model.load_state_dict(modelstate)
    loss_function = nn.BCELoss()
    model.eval()
    recall=[]
    lossestest = []
    
    y_true=[]
    y_scores=[]
    
    
    for inputs in batchtest_data:
        model.hidden = model.init_hidden()
        targets = inputs[2].cuda()
        
        tag_scores = model(inputs[0].cuda(),inputs[1].cuda() ,wikivec.cuda(),sim)

        loss = loss_function(tag_scores, targets)
        
        targets=targets.data.cpu().numpy()
        tag_scores= tag_scores.data.cpu().numpy()
        
        
        lossestest.append(loss.data.mean())
        y_true.append(targets)
        y_scores.append(tag_scores)
        
        for iii in range(0,len(tag_scores)):
            temp={}
            for iiii in range(0,len(tag_scores[iii])):
                temp[iiii]=tag_scores[iii][iiii]
            temp1=[(k, temp[k]) for k in sorted(temp, key=temp.get, reverse=True)]
            thistop=int(np.sum(targets[iii]))
            hit=0.0
            
            for ii in temp1[0:max(thistop,topk)]:
                if targets[iii][ii[0]]==1.0:
                    hit=hit+1
            if thistop!=0:
                recall.append(hit/thistop)
    y_true=np.concatenate(y_true,axis=0)
    y_scores=np.concatenate(y_scores,axis=0)
    y_true=y_true.T
    y_scores=y_scores.T
    temptrue=[]
    tempscores=[]
    for  col in range(0,len(y_true)):
        if np.sum(y_true[col])!=0:
            temptrue.append(y_true[col])
            tempscores.append(y_scores[col])
    temptrue=np.array(temptrue)
    tempscores=np.array(tempscores)
    y_true=temptrue.T
    y_scores=tempscores.T
    y_pred=(y_scores>0.5).astype(np.int)
    print ('test loss', np.mean(lossestest))
    print ('top-',topk, np.mean(recall))
    print ('macro AUC', roc_auc_score(y_true, y_scores,average='macro'))
    print ('micro AUC', roc_auc_score(y_true, y_scores,average='micro'))
    print ('macro F1', f1_score(y_true, y_pred, average='macro')  )
    print ('micro F1', f1_score(y_true, y_pred, average='micro')  )

start_test0 = timer()
print ('LSTM alone:           ')
testmodel(basemodel, 0)
end_test0 = timer()

start_test1 = timer()
print ('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
print ('KSI+LSTM:           ')
testmodel(KSImodel, 1)
end_test1 = timer()

preprocess_time = str(timedelta(seconds=start_train0-start_program))
train0_time = str(timedelta(seconds=end_train0-start_train0))
train1_time = str(timedelta(seconds=end_train1-start_train1))
test0_time = str(timedelta(seconds=end_test0-start_test0))
test1_time = str(timedelta(seconds=end_test1-start_test1))

f = open("time.txt", "a+")

f.write("\n### LSTM ###")
f.write("Preprocess: " + preprocess_time + "\n")
f.write("Train0: " + train0_time + "\n")
f.write("Train1: " + train1_time + "\n")
f.write("Test0: " + test0_time + "\n")
f.write("Test1: " + test1_time + "\n")

f.close()
