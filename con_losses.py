from __future__ import print_function

import torch
import torch.nn as nn
import torch.nn.functional as F


class SupConLoss(nn.Module):
    """Supervised Contrastive Learning: https://arxiv.org/pdf/2004.11362.pdf.
    It also supports the unsupervised contrastive loss in SimCLR"""
    def __init__(self, temperature=0.07, contrast_mode='all',
                 base_temperature=0.07, device=None):
        super(SupConLoss, self).__init__()
        self.temperature = temperature
        self.contrast_mode = contrast_mode
        self.base_temperature = base_temperature
        self.device=device

    def forward(self, features, labels=None, mask=None, adv=False):
        """Compute loss for model. If both `labels` and `mask` are None,
        it degenerates to SimCLR unsupervised loss:
        https://arxiv.org/pdf/2002.05709.pdf

        Args:
            features: hidden vector of shape [bsz, n_views, ...].
            labels: ground truth of shape [bsz].
            mask: contrastive mask of shape [bsz, bsz], mask_{i,j}=1 if sample j
                has the same class as sample i. Can be asymmetric.
        Returns:
            A loss scalar.
        """
        if self.device is not None:
            device = self.device
        else:
            device = (torch.device('cuda')
                  if features.is_cuda
                  else torch.device('cpu'))

        if len(features.shape) < 3:
            raise ValueError('`features` needs to be [bsz, n_views, ...],'
                             'at least 3 dimensions are required')
        if len(features.shape) > 3:
            features = features.view(features.shape[0], features.shape[1], -1)

        batch_size = features.shape[0]
        if labels is not None and mask is not None:
            raise ValueError('Cannot define both `labels` and `mask`')
        elif labels is None and mask is None:
            mask = torch.eye(batch_size, dtype=torch.float32).to(device)
        elif labels is not None:
            labels = labels.contiguous().view(-1, 1)
            if labels.shape[0] != batch_size:
                raise ValueError('Num of labels does not match num of features')
            mask = torch.eq(labels, labels.T).float().to(device)
        else:
            mask = mask.float().to(device)

        contrast_count = features.shape[1]
        contrast_feature = torch.cat(torch.unbind(features, dim=1), dim=0) #unbind to create n views of (k*k) tensors and concat to create (n*k) tensor
        if self.contrast_mode == 'one':
            anchor_feature = features[:, 0] #first k*k
            anchor_count = 1
        elif self.contrast_mode == 'all':
            anchor_feature = contrast_feature
            anchor_count = contrast_count
        else:
            raise ValueError('Unknown mode: {}'.format(self.contrast_mode))

        # compute logits (shape: torch.Size([256, 256])
        anchor_dot_contrast = torch.div(
            torch.matmul(anchor_feature, contrast_feature.T),
            self.temperature)
        # for numerical stability
        logits_max, _ = torch.max(anchor_dot_contrast, dim=1, keepdim=True)
        logits = anchor_dot_contrast - logits_max.detach()


        # tile mask
        mask = mask.repeat(anchor_count, contrast_count)
        # mask-out self-contrast cases
        logits_mask = torch.scatter(
            torch.ones_like(mask),
            1,
            torch.arange(batch_size * anchor_count).view(-1, 1).to(device),
            0
        )
        mask = mask * logits_mask
        # compute log_prob
        exp_logits = torch.exp(logits) * logits_mask
        #log_prob = logits - torch.log(exp_logits.sum(1, keepdim=True))
        if adv:
            log_prob = torch.log( 1- exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) - 1e-6)
        else:
            log_prob = torch.log( exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) +1e-6)

        # compute mean of log-likelihood over positive
        mean_log_prob_pos = (mask * log_prob).sum(1) / mask.sum(1)

        # loss
        loss = - (self.temperature / self.base_temperature) * mean_log_prob_pos
        loss = loss.view(anchor_count, batch_size).mean()

        return loss

#[TODO] - add ReLIC Loss
class ReLICLoss(nn.Module):
    """Supervised Contrastive Learning with ReLIC.
    It also supports the unsupervised contrastive loss in ReLIC"""
    def __init__(self, temperature=0.07, contrast_mode='all',
                 base_temperature=0.07, device=None):
        super(ReLICLoss, self).__init__()
        self.temperature = temperature
        self.contrast_mode = contrast_mode
        self.base_temperature = base_temperature
        self.device=device

    def forward(self, features, labels=None, mask=None, adv=False):
        """Compute loss for model. If both `labels` and `mask` are None,
        it degenerates to self-supervised ReLIC loss:
        https://arxiv.org/pdf/2010.07922.pdf

        Args:
            features: hidden vector of shape [bsz, n_views, ...].
            labels: ground truth of shape [bsz].
            mask: contrastive mask of shape [bsz, bsz], mask_{i,j}=1 if sample j
                has the same class as sample i. Can be asymmetric.
        Returns:
            A loss scalar.
        """
        if self.device is not None:
            device = self.device
        else:
            device = (torch.device('cuda')
                  if features.is_cuda
                  else torch.device('cpu'))

        if len(features.shape) < 3:
            raise ValueError('`features` needs to be [bsz, n_views, ...],'
                             'at least 3 dimensions are required')
        if len(features.shape) > 3:
            features = features.view(features.shape[0], features.shape[1], -1)

        batch_size = features.shape[0]
        if labels is not None and mask is not None:
            raise ValueError('Cannot define both `labels` and `mask`')
        elif labels is None and mask is None:
            mask = torch.eye(batch_size, dtype=torch.float32).to(device)
        elif labels is not None:
            labels = labels.contiguous().view(-1, 1)
            if labels.shape[0] != batch_size:
                raise ValueError('Num of labels does not match num of features')
            mask = torch.eq(labels, labels.T).float().to(device)
        else:
            mask = mask.float().to(device)

        contrast_count = features.shape[1]
        contrast_feature = torch.cat(torch.unbind(features, dim=1), dim=0) #unbind to create n views of (k*k) tensors and concat to create (n*k) tensor
        if self.contrast_mode == 'one':
            anchor_feature = features[:, 0] #first k*k
            anchor_count = 1
        elif self.contrast_mode == 'all':
            anchor_feature = contrast_feature
            anchor_count = contrast_count
        else:
            raise ValueError('Unknown mode: {}'.format(self.contrast_mode))

        # compute logits (shape: torch.Size([256, 256])
        anchor_dot_contrast = torch.div(
            torch.matmul(anchor_feature, contrast_feature.T),
            self.temperature)
        # for numerical stability
        logits_max, _ = torch.max(anchor_dot_contrast, dim=1, keepdim=True)
        logits = anchor_dot_contrast - logits_max.detach()


        # tile mask
        mask = mask.repeat(anchor_count, contrast_count)
        # mask-out self-contrast cases
        logits_mask = torch.scatter(
            torch.ones_like(mask),
            1,
            torch.arange(batch_size * anchor_count).view(-1, 1).to(device),
            0
        )
        

        mask = mask * logits_mask #Mask Shape: torch.Size([256, 256]) / Logits Shape: torch.Size([256, 256])
        # compute log_prob
        exp_logits = torch.exp(logits) * logits_mask #Exp Logits Shape: torch.Size([256, 256])
        
        #log_prob = logits - torch.log(exp_logits.sum(1, keepdim=True))
        if adv:
            log_prob = torch.log( 1- exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) - 1e-6)
        else:
            log_prob = torch.log( exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) +1e-6)

        # compute mean of log-likelihood over positive
        mean_log_prob_pos = (mask * log_prob).sum(1) / mask.sum(1)

        # loss
        loss = - (self.temperature / self.base_temperature) * mean_log_prob_pos
        loss = loss.view(anchor_count, batch_size).mean()  # This is the contrastive loss. 

        return loss

#[TODO] - add BarlowTwins Loss
class BarlowTwinsLoss(nn.Module):
    """Supervised Contrastive Learning with ReLIC.
    It also supports the unsupervised contrastive loss in ReLIC"""
    def __init__(self, temperature=0.07, contrast_mode='all',
                 base_temperature=0.07, device=None):
        super(BarlowTwinsLoss, self).__init__()
        self.temperature = temperature
        self.contrast_mode = contrast_mode
        self.base_temperature = base_temperature
        self.device=device
        #self.bn = nn.BatchNorm1d(sizes[-1], affine=False)

    def forward(self, features, labels=None, mask=None, adv=False):
        """Compute loss for model. If both `labels` and `mask` are None,
        it degenerates to self-supervised BarlowTwins loss:
        https://arxiv.org/pdf/2103.03230v3.pdf

        Args:
            features: hidden vector of shape [bsz, n_views, ...].
            labels: ground truth of shape [bsz].
            mask: contrastive mask of shape [bsz, bsz], mask_{i,j}=1 if sample j
                has the same class as sample i. Can be asymmetric.
        Returns:
            A loss scalar.
        """
        if self.device is not None:
            device = self.device
        else:
            device = (torch.device('cuda')
                  if features.is_cuda
                  else torch.device('cpu'))

        if len(features.shape) < 3:
            raise ValueError('`features` needs to be [bsz, n_views, ...],'
                             'at least 3 dimensions are required')
        if len(features.shape) > 3:
            features = features.view(features.shape[0], features.shape[1], -1)

        batch_size = features.shape[0]
        if labels is not None and mask is not None:
            raise ValueError('Cannot define both `labels` and `mask`')
        elif labels is None and mask is None:
            mask = torch.eye(batch_size, dtype=torch.float32).to(device)
        elif labels is not None:
            labels = labels.contiguous().view(-1, 1)
            if labels.shape[0] != batch_size:
                raise ValueError('Num of labels does not match num of features')
            mask = torch.eq(labels, labels.T).float().to(device)
        else:
            mask = mask.float().to(device)
        
        contrast_count = features.shape[1] #features.shape= torch.Size([128, 2, 128])
        contrast_feature = torch.cat(torch.unbind(features, dim=1), dim=0) #unbind to create n views of (k*k) tensors and concat to create (n*k) tensor - (torch.Size([256, 128]))
        
        if self.contrast_mode == 'one':
            anchor_feature = features[:, 0] #first k*k --torch.Size([128, 128])
            anchor_count = 1
        elif self.contrast_mode == 'all':
            anchor_feature = contrast_feature # torch.Size([256, 128])
            anchor_count = contrast_count
        else:
            raise ValueError('Unknown mode: {}'.format(self.contrast_mode))
        #BARLOW TWINS
        def off_diagonal(x):
            # return a flattened view of the off-diagonal elements of a square matrix
            n, m = x.shape
            assert n == m
            return x.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()
        #{TODO}- 1. Normalize representation along the batch dimension
        anchor_feature= (anchor_feature - anchor_feature.mean(0)) / anchor_feature.std(0)
        contrast_feature = (contrast_feature - contrast_feature.mean(0)) / contrast_feature.std(0)
        #anchor_feature,contrast_feature = self.bn(anchor_feature), self.bn(contrast_feature)
        #{TODO}- 2. MatMul for cross-correlation matrix
        c= torch.matmul(anchor_feature, contrast_feature.T) / batch_size
        c.div_(batch_size)
        #{TODO}- 3. Loss
        #c_diff= (c- torch.eye(anchor_feature.shape)).pow(2)
        on_diag = torch.diagonal(c).add_(-1).pow_(2).sum()
        off_diag = off_diagonal(c).pow_(2).sum()
        loss = on_diag + 0.0051 * off_diag
        
        #Unfreeze to SupConLoss
        '''
        # compute logits (shape: torch.Size([256, 256]) #Matrix Multiplication
        anchor_dot_contrast = torch.div(
            torch.matmul(anchor_feature, contrast_feature.T),
            self.temperature)
        # for numerical stability
        logits_max, _ = torch.max(anchor_dot_contrast, dim=1, keepdim=True)
        logits = anchor_dot_contrast - logits_max.detach()


        # tile mask
        mask = mask.repeat(anchor_count, contrast_count)
        # mask-out self-contrast cases
        logits_mask = torch.scatter(
            torch.ones_like(mask),
            1,
            torch.arange(batch_size * anchor_count).view(-1, 1).to(device),
            0
        )

        mask = mask * logits_mask #Mask Shape: torch.Size([256, 256])
        # compute log_prob
        exp_logits = torch.exp(logits) * logits_mask #Exp Logits Shape: torch.Size([256, 256])
        
        #log_prob = logits - torch.log(exp_logits.sum(1, keepdim=True))
        if adv:
            log_prob = torch.log( 1- exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) - 1e-6)
        else:
            log_prob = torch.log( exp_logits / (exp_logits.sum(1, keepdim=True)+1e-6) +1e-6)

        # compute mean of log-likelihood over positive
        mean_log_prob_pos = (mask * log_prob).sum(1) / mask.sum(1)

        # loss
        loss = - (self.temperature / self.base_temperature) * mean_log_prob_pos
        loss = loss.view(anchor_count, batch_size).mean()  # This is the contrastive loss. 
        '''
        
        return loss


if __name__=='__main__':
    import torch.nn.functional as F
    torch.manual_seed(0)
    x = torch.randn(32, 2, 10)
    x = F.normalize(x)
    y = torch.randint(0, 10, [32])
    loss_layer = SupConLoss()
    loss = loss_layer(x, y)
    print(loss)

