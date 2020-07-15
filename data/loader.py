import pandas as pd
import numpy as np
import torch
from copy import deepcopy


class cryptoData(object):

    def __init__(self,currency,test = False,DEVICE = torch.device("cpu"),window=7,model=None):
        data = pd.read_csv("data/data/"+currency+"Final.csv")
        window = 7
        data = data.drop(["Unnamed: 0",
                        "Unnamed: 0_x",
                        "timestamp",
                        "datetime",
                        "index",
                        "top100cap-"+currency,
                        "mediantransactionvalue-"+currency,
                        "Unnamed: 0_y"
                        ], axis=1)
        self.test = test

        if currency == "btc":
            var = "bitcoin-price"
        elif currency == "eth":
            var = "ethereum-price"
        else:
            var = "litecoin-price"

        data = data.iloc[:851]
        train_data = data.iloc[:650]
        test_data = data.iloc[650:]
        self.raw = data

        price = np.asarray(data[var])
        mean = train_data.mean()
        self.raw_prices = deepcopy(price)

        train_data = train_data/mean
        test_data = test_data/mean
        self.raw = self.raw/mean
        
        train_data = torch.Tensor(train_data.to_numpy())
        test_data = torch.Tensor(test_data.to_numpy())
        self.raw = torch.Tensor(self.raw.to_numpy())

        train_data[:,5] = torch.Tensor(price[:650])
        test_data[:,5] = torch.Tensor(price[650:])
        self.raw[:,5] = torch.Tensor(self.raw_prices[:])
        self.raw_prices = torch.Tensor(self.raw_prices)

        xtrain = []
        ytrain = []
        self.window = window
        for i in range(len(train_data)-window):
            xtrain.append(np.asarray(train_data[i:i+window,:]))
            ytrain.append(np.asarray(train_data[i+window][5]))

        self.xtrain = torch.Tensor(np.asarray(xtrain)).to(DEVICE)
        self.ytrain = torch.Tensor(np.asarray(ytrain)).to(DEVICE)

        if model == None or model== "norm":
            self.pmax = torch.mean(self.ytrain)
        elif model == "unorm":
            self.pmax = torch.Tensor([1])

        xtest = []
        ytest = []
        for i in range(len(test_data)-window):
            xtest.append(np.asarray(test_data[i:i+window,:]))
            ytest.append(np.asarray(test_data[i+window][5]))

        self.xtest = torch.Tensor(np.asarray(xtest)).to(DEVICE)
        self.ytest = torch.Tensor(np.asarray(ytest)).to(DEVICE)

        self.xtrain[:,:,5] /= self.pmax
        self.ytrain = self.ytrain/self.pmax
        self.xtest[:,:,5] = self.xtest[:,:,5]/self.pmax
        self.ytest = self.ytest/self.pmax
        self.raw /= self.pmax

    def __getitem__(self,key):
        if not self.test:
            seven_day_data = self.xtrain[key]
            target = self.ytrain[key].view(1,1)
        else:
            seven_day_data = self.xtest[key]
            target  = self.ytest[key].view(1,1)
        return seven_day_data, target

    
    def __len__(self):
        if self.test:
            return 230-self.window
        return 650-self.window

    def getDataFrame(self,maxRange):
        prices = self.raw_prices[:maxRange]
        return prices.view(-1,1),torch.mean(prices),torch.std(prices)