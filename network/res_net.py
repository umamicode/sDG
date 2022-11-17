
import torch
import torch.nn as nn
import torch.nn.functional as F

import torchvision

from network.modules.resnet_hacks import modify_resnet_model
from network.modules.identity import Identity

#[TODO]-added for check
torch.autograd.set_detect_anomaly(True)

class ConvNet(nn.Module):
    ''' The network structure is consistent with the SimCLR method
     '''
    def __init__(self, encoder, projection_dim, n_features, output_dim, imdim=3):
        super(ConvNet, self).__init__()
        '''
        self.conv1 = nn.Conv2d(imdim, 64, kernel_size=5, stride=1, padding=0)
        self.mp = nn.MaxPool2d(2)
        self.relu1 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.conv2 = nn.Conv2d(64, 128, kernel_size=5, stride=1, padding=0)
        self.relu2 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.fc1 = nn.Linear(128*5*5, 1024)
        self.relu3 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.fc2 = nn.Linear(1024, 1024)
        self.relu4 = nn.ReLU(inplace=False) #TODO- inplace=True
        '''
        #added 
        self.encoder= encoder
        self.projection_dim= projection_dim
        self.n_features= n_features
        self.output_dim= output_dim
        
        # Replace the fc layer with an Identity function
        self.encoder.fc = Identity()
        
        self.cls_head_src = nn.Linear(self.n_features, self.output_dim)
        self.cls_head_tgt = nn.Linear(self.n_features, self.output_dim)
        #self.pro_head = nn.Linear(self.n_features, self.projection_dim)
        #[TODO]- MLP for Contrastive Learning
        self.pro_head = nn.Sequential(
            nn.Linear(self.n_features, self.n_features, bias=False),
            nn.ReLU(),
            nn.Linear(self.n_features, self.projection_dim, bias=False),
        )

    def forward(self, x, mode='test'):
        in_size = x.size(0)
        '''
        out1 = self.mp(self.relu1(self.conv1(x)))
        out2 = self.mp(self.relu2(self.conv2(out1)))
        out2 = out2.view(in_size, -1)
        out3 = self.relu3(self.fc1(out2))
        out4 = self.relu4(self.fc2(out3))
        '''
        out4= self.encoder(x)
        
        if mode == 'test':
            p = self.cls_head_src(out4)
            return p
        elif mode == 'train':
            p = self.cls_head_src(out4)
            z = self.pro_head(out4)
            z = F.normalize(z)
            return p,z
        elif mode == 'p_f':
            p = self.cls_head_src(out4)
            return p, out4
        #elif mode == 'target':
        #    p = self.cls_head_tgt(out4)
        #    z = self.pro_head(out4)
        #    z = F.normalize(z)
        #    return p,z
    
class ConvNetVis(nn.Module):
    ''' 
    For easy visualization, the feature extractor outputs 2-d features
    '''
    def __init__(self, imdim=3):
        super(ConvNetVis, self).__init__()

        self.conv1 = nn.Conv2d(imdim, 64, kernel_size=5, stride=1, padding=0)
        self.mp = nn.MaxPool2d(2)
        self.relu1 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.conv2 = nn.Conv2d(64, 128, kernel_size=5, stride=1, padding=0)
        self.relu2 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.fc1 = nn.Linear(128*5*5, 1024)
        self.relu3 = nn.ReLU(inplace=False) #TODO- inplace=True
        self.fc2 = nn.Linear(1024, 2)
        self.relu4 = nn.ReLU(inplace=False) #TODO- inplace=True
        
        self.cls_head_src = nn.Linear(2, 10)
        self.cls_head_tgt = nn.Linear(2, 10)
        self.pro_head = nn.Linear(2, 128)

    def forward(self, x, mode='test'):
        in_size = x.size(0)
        out1 = self.mp(self.relu1(self.conv1(x)))
        out2 = self.mp(self.relu2(self.conv2(out1)))
        out2 = out2.view(in_size, -1)
        out3 = self.relu3(self.fc1(out2))
        out4 = self.relu4(self.fc2(out3))
        



        if mode == 'test':
            p = self.cls_head_src(out4)
            return p
        elif mode == 'train':
            p = self.cls_head_src(out4)
            z = self.pro_head(out4)
            z = F.normalize(z)
            return p,z
        elif mode == 'p_f':
            p = self.cls_head_src(out4)
            return p, out4
        #elif mode == 'target':
        #    p = self.cls_head_tgt(out4)
        #    z = self.pro_head(out4)
        #    z = F.normalize(z)
        #    return p,z
    
