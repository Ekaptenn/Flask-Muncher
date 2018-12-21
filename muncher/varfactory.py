#!/usr/bin/env python
# Copyright 2011 Craig Campbell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
from array import array

class VarFactory:
    """class to keep multiple counters and turn numeric counters into alphabetical ones"""
    types = {}
    letters = map(chr, range(97, 123))

    @staticmethod
    def getNext(type):
        """gets the next letter name based on counter name

        Arguments:
        type -- name of counter we want the next value for

        Returns:
        string

        """
        i = VarFactory.getVersion(type)
        return VarFactory.getSmallName(i)

    @staticmethod
    def getVersion(type):
        """gets the next number in the counter for this type

        Arguments:
        type -- name of counter we are incrementing

        Resturns:
        int

        """
        if not type in VarFactory.types:
            VarFactory.types[type] = 0
            return 0

        VarFactory.types[type] += 1

        return VarFactory.types[type]

    @staticmethod
    def getSmallName(index):
        """gets a letter index based on the numeric index

        Arguments:
        index -- the number you are looking for

        Returns:
        string

        """
        #print index,'$'
        symbols = array('c', ["a", "b", "c", "d", "e", "f", "g", "h",
        "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

        return symbols[index / (len(symbols) * len(symbols))] + symbols[(index / len(symbols)) % len(symbols)]+symbols[index % len(symbols)]
