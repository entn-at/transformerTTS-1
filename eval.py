import torch
import torch.nn as nn
import argparse
import numpy as np
import random
import time
import shutil
import os

import hparams as hp
import audio
import utils
import dataset
import text
import model as M
import waveglow

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def get_DNN(num):
    checkpoint_path = "checkpoint_" + str(num) + ".pth.tar"
    model = nn.DataParallel(M.Tacotron2(hp)).to(device)
    model.load_state_dict(torch.load(os.path.join(hp.checkpoint_path,
                                                  checkpoint_path))['model'])
    model.eval()
    return model


def synthesis(model, text):
    text = np.array(phn)
    text = np.stack([text])
    sequence = torch.from_numpy(text).cuda().long()

    with torch.no_grad():
        _, mel, _, _ = model.module.inference(sequence)
    return mel[0].cpu(), mel.contiguous()


def get_data():
    test1 = "I am very happy to see you again!"
    test2 = "Durian model is a very good speech synthesis!"
    test3 = "When I was twenty, I fell in love with a girl."
    test4 = "I remove attention module in decoder and use average pooling to implement predicting r frames at once"
    test5 = "You can not improve your past, but you can improve your future. Once time is wasted, life is wasted."
    test6 = "Death comes to all, but great achievements raise a monument which shall endure until the sun grows old."
    data_list = list()
    data_list.append(text.text_to_sequence(test1, hp.text_cleaners))
    data_list.append(text.text_to_sequence(test2, hp.text_cleaners))
    data_list.append(text.text_to_sequence(test3, hp.text_cleaners))
    data_list.append(text.text_to_sequence(test4, hp.text_cleaners))
    data_list.append(text.text_to_sequence(test5, hp.text_cleaners))
    data_list.append(text.text_to_sequence(test6, hp.text_cleaners))
    return data_list


if __name__ == "__main__":
    # Test
    WaveGlow = utils.get_WaveGlow()
    print("load waveglow")
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, default=0)
    args = parser.parse_args()

    print("use griffin-lim and waveglow")
    model = get_DNN(args.step)
    data_list = get_data()
    for i, phn in enumerate(data_list):
        mel, mel_cuda = synthesis(model, phn)
        if not os.path.exists("results"):
            os.mkdir("results")
        audio.tools.inv_mel_spec(
            mel, "results/"+str(args.step)+"_"+str(i)+".wav")
        waveglow.inference.inference(
            mel_cuda, WaveGlow,
            "results/"+str(args.step)+"_"+str(i)+"_waveglow.wav")
        print("Done", i + 1)
