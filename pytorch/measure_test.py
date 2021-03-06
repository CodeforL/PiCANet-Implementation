# from sklearn.metrics import precision_recall_fscore_support
from network import Unet
from dataset import DUTSDataset
import torch
import os
import torch.nn.functional as F
import numpy as np
from torch.utils.data import DataLoader
from tensorboardX import SummaryWriter

import argparse
from sklearn.metrics import precision_recall_curve

torch.set_printoptions(profile='full')
if __name__ == '__main__':

    models = sorted(os.listdir('models/state_dict/07121619'), key=lambda x: int(x.split('epo_')[1].split('step')[0]))
    duts_dataset = DUTSDataset(root_dir='../DUTS-TE', train=False)
    dataloader = DataLoader(duts_dataset, 4, shuffle=True)
    beta_square = 0.3
    device = torch.device("cuda")
    writer = SummaryWriter('log/F_Measure')
    model = Unet().to(device)
    for model_name in models:
        if int(model_name.split('epo_')[1].split('step')[0]) < 79000:
            continue
        if int(model_name.split('epo_')[1].split('step')[0]) % 1000 != 0:
            continue

        state_dict = torch.load('models/state_dict/07121619/' + model_name)
        model.load_state_dict(state_dict)
        model.eval()
        mse = 0
        preds = []
        masks = []
        for i, batch in enumerate(dataloader):
            img = batch['image'].to(device)
            mask = batch['mask'].to(device)
            with torch.no_grad():
                pred, loss = model(img, mask)
            pred = pred[5].data
            mse += F.mse_loss(pred, mask)
            pred = pred.requires_grad_(False)
            preds.append(pred)
            masks.append(mask)
            if not i < 100:
                break
        pred = torch.stack(preds, 0)
        mask = torch.stack(masks, 0)
        writer.add_pr_curve('PR_curve', mask, pred, global_step=int(model_name.split('epo_')[1].split('step')[0]))
        writer.add_scalar('MAE', F.mse_loss(pred, mask), global_step=int(model_name.split('epo_')[1].split('step')[0]))
        prediction = pred.data.cpu().numpy().flatten()
        target = mask.data.round().cpu().numpy().flatten()
        # print(type(prediction))
        precision, recall, threshold = precision_recall_curve(target, prediction)
        f_score = (1 + beta_square) * precision * recall / (beta_square * precision + recall)
        writer.add_scalar("Max F_score", np.max(f_score), global_step=int(model_name.split('epo_')[1].split('step')[0]))
        writer.add_scalar("Max_F_threshold", threshold[np.argmax(f_score)], global_step=int(model_name.split('epo_')[1].split('step')[0]))
        print(model_name.split('epo_')[1].split('step')[0])
        """
        for edge in range(100):
            threshold = edge/100.0
            avg_precision, avg_recall, avg_fscore = [], [], []
            tp, tn, fp, fn, = 0, 0, 0, 0
            for i, batch in enumerate(dataloader):
                img = batch['image'].to(device)
                mask = batch['mask'].to(device)
                with torch.no_grad():
                    pred, loss = model(img, mask)
                pred = pred[5].data
                writer.add_pr_curve('1234', mask, pred)
                mse += F.mse_loss(pred, mask)
                pred = pred.requires_grad_(False)
                pred = torch.round(pred + threshold - 0.5).data
                t = mask.type(torch.cuda.FloatTensor)
                p = pred.type(torch.cuda.FloatTensor)
                f = 1 - mask.type(torch.cuda.FloatTensor)
                n = 1 - pred.type(torch.cuda.FloatTensor)
                # based on http://blog.acronym.co.kr/556
                tp += float(torch.sum(t * p))
                tn += float(torch.sum(f * n))
                fp += float(torch.sum(f * p))
                fn += float(torch.sum(t * n))
                if i % 100 == 0 and i > 0:
                    print('Model: '+model_name)
                    print('i: ', i)
                    print('tp: '+str(tp))
                    print('tn: '+str(tn))
                    print('fp: '+str(fp))
                    print('fn: '+str(fn))
                    break
            precision = tp / (tp + fp)
            recall = tp / (tp + fn)
            fscore = (1 + beta_square) * precision * recall / (beta_square * precision + recall)
            writer.add_scalar('precision', precision, global_step=int(model_name.split('epo_')[1].split('step')[0]))
            writer.add_scalar('recall', recall, global_step=int(model_name.split('epo_')[1].split('step')[0]))
            writer.add_scalar('F_score', fscore, global_step=int(model_name.split('epo_')[1].split('step')[0]))
            print('Model : ' + model_name)
            print('Threshold : '+str(threshold))
            print('Precision : ' + str(precision))
            print('Recall : ' + str(recall))
            print('F_score : ' + str(fscore))
        print('MAE:' + str(mse / 10000))
        writer.add_scalar('MAE', mse / 10000, global_step=int(model_name.split('epo_')[1].split('step')[0]))
        """