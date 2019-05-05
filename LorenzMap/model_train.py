# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


import sys
import time
import os

from mxnet import autograd, gluon, nd
from tqdm import trange

from net_builder import LorenzBuilder
from metric_util import plot_losses
# pylint: disable=invalid-name, too-many-arguments, too-many-instance-attributes, no-member, no-self-use


class Train(object):
    """
    Training engine for Lorenz architecture.
    """

    def __init__(self, options):
        self._options = options

    def save_model(self, net):
        net.save_params(os.path.join(self._options.check_path, 'best_perf_model'))

    def train(self, train_iter):

        net = LorenzBuilder(self._options, for_train=True).build()
        trainer = gluon.Trainer(net.collect_params(),
                                'adam', {'learning_rate': self._options.learning_rate,
                                         'wd': self._options.l2_regularization})

        loss = gluon.loss.L1Loss()

        loss_save = []
        best_loss = sys.maxsize

        start = time.time()

        for epoch in trange(self._options.epochs):
            total_epoch_loss, nb = 0, 0
            for x, y in train_iter:
                # x shape: (batch_sizeXin_channelsXwidth)
                x = x.reshape((self._options.batch_size, self._options.in_channels, -1))
                # print(x.shape)
                nb += 1
                with autograd.record():
                    y_hat = net(x)
                    l = loss(y_hat, y)
                    total_epoch_loss += nd.sum(l).asscalar()
                l.backward()
                trainer.step(self._options.batch_size, ignore_stale_grad=True)

            current_loss = total_epoch_loss / nb
            loss_save.append(current_loss)
            print('Epoch {}, loss {}'.format(epoch, current_loss))

            if current_loss < best_loss:
                best_loss = current_loss
                self.save_model(net)
            print('best epoch loss: ', best_loss)

        end = time.time()
        print("Process took ", end - start, " seconds.")

        if self._options.plot_losses:
            plt = plot_losses(loss_save, 'w')
            plt.show()
            plt.savefig(os.path.join(self._options.assets_dir, 'losses_w'))
            plt.close()

