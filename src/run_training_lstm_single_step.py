import os.path
from models.lstm import LSTM
from train.train_lstm_single_step import train, evaluate, predict_batches
import reader
import torch
from torch import optim
import numpy as np
from matplotlib import pyplot as plt

use_cuda = False
checkpoint_file = "../checkpoints/simple_lstm/model.pt"

input_size = 3
output_size = 1
hidden_size = 200
n_layers = 1
lr = 0.001
batch_size = 32
n_epochs = 300
input_seq_len = 30
output_seq_len = 1

data_path = "../data/count_by_hour_with_header.csv"
data_scaled = reader.get_scaled_mrt_data(data_path, [0], datetime_features=True, holidays=None)
x = np.expand_dims(data_scaled[:-1], 1)
y = data_scaled[1:, 0]
y = y.reshape(y.shape[0], 1, 1)

x = torch.from_numpy(x).contiguous()
y = torch.from_numpy(y).contiguous()

num_train = round(x.shape[0] * 0.6)
num_val = round(x.shape[0] * 0.2)
num_test = num_val

x_train = x[0:num_train]
y_train = y[0:num_train]

n_sequences_train = x_train.shape[0] // input_seq_len
x_train = x_train[0:n_sequences_train * input_seq_len]
y_train = y_train[0:n_sequences_train * input_seq_len]
x_train = x_train.view([n_sequences_train, input_seq_len, 1, input_size])
y_train = y_train.view([n_sequences_train, input_seq_len, 1, output_size])


x_val = x[num_train:num_train + num_val]
y_val = y[num_train:num_train + num_val]
n_sequences_val = x_val.shape[0] // input_seq_len
x_val = x_val[0:n_sequences_val * input_seq_len]
y_val = y_val[0:n_sequences_val * input_seq_len]
x_val = x_val.view([n_sequences_val, input_seq_len, 1, input_size])
y_val = y_val.view([n_sequences_val, input_seq_len, 1, output_size])



x_test = x[num_train + num_val:]
y_test = y[num_train + num_val:]


lstm = LSTM(input_size, hidden_size, output_size, n_layers)

if os.path.isfile(checkpoint_file):
    print("Loading checkpoint...")
    lstm.load_state_dict(torch.load(checkpoint_file))

if use_cuda:
    lstm.cuda()

lstm.hidden = lstm.init_hidden(1)

# predictions = predict_batches(x_val, lstm, use_cuda=use_cuda)
# plt.plot(predictions.numpy().flatten())
# plt.plot(y_val.numpy().flatten())
# plt.show()

optimizer = optim.Adam(lstm.parameters(), lr=lr)

best_val_loss = 1000
for epoch in range(n_epochs):
    n_batches = x_train.shape[0]
    for i in range(n_batches):
        lstm.hidden = None
        input_batches = x_train[i]
        target_batches = y_train[i]
        train_loss = train(input_batches, target_batches, lstm, optimizer, use_cuda)


    epoch_train_loss = evaluate(x_train, y_train, lstm)
    epoch_val_loss = evaluate(x_val, y_val, lstm)

    print("epoch %i/%i" % (epoch + 1, n_epochs))
    print("traing loss is %f, validation loss is %f" % (epoch_train_loss, epoch_val_loss))

    if epoch_val_loss < best_val_loss:
        print("Saving the model...")
        best_val_loss = epoch_val_loss
        torch.save(lstm.state_dict(), checkpoint_file)