#coding:utf-8
import numpy as np
import torch
import GRCNN
from torch.autograd import Variable
import cv2
import os
from glob import glob
import utils
import shutil
import argparse
import csv

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

parser = argparse.ArgumentParser(description='PyTorch GRCNN Evaluation')

parser.add_argument('--is_use_gpu', default=False, type=bool, help='is use gpu')
parser.add_argument('--gpu_list', default='-1', type=str, help='gpu_list')
parser.add_argument('--img_w', default=300, type=int, help='the width of image')
parser.add_argument('--img_h', default=45, type=int, help='the height of image')
parser.add_argument('--n_class', default=37, type=int, help='the number of class')
parser.add_argument('--alphabet', default='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', type=str, help='alphabet')
parser.add_argument('--pre_train_model_path', default='./model_result/cpu_model_parameter_1.pkl', type=str, help='pretraining model path')
parser.add_argument('--test_data_path', default='./data_sample/', type=str, help='test data set path')
parser.add_argument('--test_result_save_path', default='./test_result/', type=str, help='result save path')

args = parser.parse_args()

if args.is_use_gpu:
    os.environ['CUDA_VISIBLE_DEVICES']=args.gpu_list

if os.path.exists(args.test_result_save_path):
    shutil.rmtree(args.test_result_save_path)
os.mkdir(args.test_result_save_path)

test_img_list = sorted(glob(args.test_data_path + '*.jpg'))


crnn = GRCNN.GRCNN(args.n_class)
crnn.load_state_dict(torch.load(args.pre_train_model_path))

if args.is_use_gpu:
    crnn = crnn.to(device)
print('net has load!')
converter = utils.strLabelConverter(args.alphabet)
crnn.eval()


def get_img(img_path):
    img = cv2.imread(img_path)
    img= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img = cv2.resize(img, (args.img_w, args.img_h))
    img = np.reshape(img, newshape=[1,1, args.img_h, args.img_w])
    img = img.astype(np.float32)
    img = img / 255
    img = img - 0.5
    img = img * 2
    img_tensor = torch.from_numpy(img).float()
    return img_tensor

with open('prediction_table.csv', 'w', newline='') as csvfile:
    for img_path in test_img_list:
        img_tensor = get_img(img_path)
        if args.is_use_gpu:
            img_tensor = Variable(img_tensor).to(device)
        else:
            img_tensor = Variable(img_tensor)
        preds = crnn(img_tensor)
        _, preds = preds.max(2)
        preds = preds.transpose(1, 0).contiguous().view(-1)
        preds_size = Variable(torch.IntTensor([preds.size(0)]))
        raw_pred = converter.decode(preds.data, preds_size.data, raw=True)
        sim_pred = converter.decode(preds.data, preds_size.data, raw=False)
    
    
        spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow([img_path, sim_pred])
        
        print(f'{img_path} -> {sim_pred}')




