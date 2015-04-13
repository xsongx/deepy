#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import NeuralLayer
from deepy.util import build_activation, FLOATX
import numpy as np
import theano
import theano.tensor as T

OUTPUT_TYPES = ["last_hidden", "all_hidden", "last_output", "all_output"]
INPUT_TYPES = ["sequence", "one"]

class RNN(NeuralLayer):
    """
    Recurrent neural network layer.
    """

    def __init__(self, hidden_size, output_size=None, input_type="sequence", output_type="last_hidden",
                 activation="tanh", hidden_initializer=None, initializer=None, steps=None):
        super(RNN, self).__init__("rnn")
        self._hidden_size = hidden_size
        self._output_size = output_size
        self._input_type = input_type
        self._output_type = output_type
        self._activation = activation
        self._hidden_initializer = hidden_initializer
        self._initializer = hidden_initializer
        self._steps = steps
        if input_type not in INPUT_TYPES:
            raise Exception("Input type of RNN is wrong: %s" % input_type)
        if output_type not in OUTPUT_TYPES:
            raise Exception("Output type of RNN is wrong: %s" % output_type)


    def _step(self, *variables):
        if self._input_type == "sequence":
            x, h = variables
            z = T.dot(x, self.W_i) + T.dot(h, self.W_h) + self.B_h
        else:
            h, = variables
            z = T.dot(h, self.W_h) + self.B_h

        new_h = self._activation_func(z)
        if "output" in self._output_type:
            o = self._activation_func(T.dot(new_h, self.W_o) + self.B_o)
            return new_h, o
        else:
            return new_h


    def output(self, x):
        sequences = []
        h0 = T.alloc(np.cast[FLOATX](0.), x.shape[0], self._hidden_size)
        if self._input_type == "sequence":
            # Move middle dimension to left-most position
            # (sequence, batch, value)
            sequences = [x.dimshuffle((1,0,2))]
        else:
            h0 = x
        step_outputs = [h0]
        if "output" in self._output_type:
            step_outputs = [h0, None]
        output_vars, _ = theano.scan(self._step, sequences=sequences, outputs_info=step_outputs, n_steps=self._steps)
        if "output" in self._output_type:
            _, os = output_vars
            if self._output_type == "last_output":
                return os[-1]
            elif self._output_type == "all_output":
                return os.dimshuffle((1,0,2))
        else:
            hs = output_vars
            if self._output_type == "last_hidden":
                return hs[-1]
            elif self._output_type == "all_hidden":
                return hs.dimshuffle((1,0,2))

    def setup(self):
        self._setup_params()
        self._setup_functions()

    def _setup_functions(self):
        self._activation_func = build_activation(self._activation)

    def _setup_params(self):
        self.W_h = self.create_weight(self._hidden_size, self._hidden_size, suffix="h", initializer=self._hidden_initializer)
        self.B_h = self.create_bias(self._hidden_size, suffix="h")

        self.register_parameters(self.W_h, self.B_h)

        if self._input_type == "sequence":
            self.W_i = self.create_weight(self.input_dim, self._hidden_size, suffix="i", initializer=self._initializer)
            self.register_parameters(self.W_i)

        if "output" in self._output_type:
            assert self._output_size
            self.W_o = self.create_weight(self._hidden_size, self._output_size, suffix="o",  initializer=self._initializer)
            self.B_o = self.create_bias(self._output_size, suffix="o")
            self.register_parameters(self.W_o, self.B_o)
            self.output_dim = self._output_size
        elif "hidden" in self._output_type:
            self.output_dim = self._hidden_size
