import os
import json
import torch
import argparse
import numpy as np

from models.rnn_vae import RNNVAE
from models.transformer_vae import TransformerVAE
from utils import decode_sentnece_from_token


def main(args):
    vocab_file = os.path.join(args.data_dir, 'vocab.json')
    vocab = json.load(open(vocab_file, 'r') )

    w2i, i2w = vocab['w2i'], vocab['i2w']

    if args.model == 'rnn':
        model = RNNVAE(
            rnn_type=args.rnn_type,
            num_embeddings=len(w2i),
            dim_embedding=args.dim_embedding,
            dim_hidden=args.dim_hidden, 
            num_layers=args.num_layers,
            bidirectional=args.bidirectional, 
            dim_latent=args.dim_latent, 
            word_dropout=args.word_dropout,
            dropout=args.dropout,
            sos_idx=w2i['<sos>'],
            eos_idx=w2i['<eos>'],
            pad_idx=w2i['<pad>'],
            unk_idx=w2i['<unk>'],
            max_sequence_length=args.max_sequence_length).to(device)
    elif args.model == 'transformer':
        model = TransformerVAE(
            num_embeddings=len(w2i),
            dim_model=args.dim_model,
            nhead=args.nhead,
            dim_feedforward=args.dim_feedforward,
            num_layers=args.num_layers,
            dim_latent=args.dim_latent, 
            word_dropout=args.word_dropout,
            dropout=args.dropout,
            sos_idx=w2i['<sos>'],
            eos_idx=w2i['<eos>'],
            pad_idx=w2i['<pad>'],
            unk_idx=w2i['<unk>'],
            max_sequence_length=args.max_sequence_length).to(device)
    else:
        raise ValueError

    if not os.path.exists(args.load_checkpoint):
        raise FileNotFoundError(args.load_checkpoint)

    model.load_state_dict(torch.load(args.load_checkpoint))
    print("Model loaded from %s\n"%(args.load_checkpoint))


    # sample
    print('----------SAMPLES----------')
    model.eval()
    zs = torch.randn(args.num_samples, args.dim_latent)
    for i in range(len(zs)):
        z = zs[i].unsqueeze(0)
        output = model.infer(z)
        print(decode_sentnece_from_token(output[0].tolist(), i2w))
    print()

    print('-------INTERPOLATION-------')
    z1 = torch.randn([args.dim_latent]).numpy()
    z2 = torch.randn([args.dim_latent]).numpy()
    interpolation = np.zeros((args.dim_latent, args.num_samples))
    for dim, (s,e) in enumerate(zip(z1,z2)):
        interpolation[dim] = np.linspace(s, e, args.num_samples)
    interpolation = interpolation.T

    zs = torch.from_numpy(interpolation).float()
    for i in range(len(zs)):
        z = zs[i].unsqueeze(0)
        output = model.infer(z)
        print(decode_sentnece_from_token(output[0].tolist(), i2w))

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--load_checkpoint', type=str)
    parser.add_argument('-n', '--num_samples', type=int, default=10)

    parser.add_argument('--data_dir', type=str, default='data')
    parser.add_argument('--max_sequence_length', type=int, default=60)

    # model settings
    parser.add_argument('-dl', '--dim_latent', type=int, default=64)
    parser.add_argument('-nl', '--num_layers', type=int, default=1)
    parser.add_argument('-wd', '--word_dropout', type=float, default=0.6)
    parser.add_argument('-do', '--dropout', type=float, default=0.5)

    # rnn settings
    parser.add_argument('-de', '--dim_embedding', type=int, default=300)
    parser.add_argument('-rnn', '--rnn_type', type=str, default='gru')
    parser.add_argument('-dh', '--dim_hidden', type=int, default=256)
    parser.add_argument('-bi', '--bidirectional', action='store_true')

    # transformer settings
    parser.add_argument('-dm', '--dim_model', type=int, default=256)
    parser.add_argument('-nh', '--nhead', type=int, default=4)
    parser.add_argument('-df', '--dim_feedforward', type=int, default=256)

    args = parser.parse_args()

    main(args)
