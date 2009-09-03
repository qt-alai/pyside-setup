'''
This file is part of the Shiboken Python Bindings Generator project.

Copyright (C) 2009 Nokia Corporation and/or its subsidiary(-ies).

Contact: PySide team <contact@pyside.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License
version 2.1 as published by the Free Software Foundation. Please
review the following information to ensure the GNU Lesser General
Public License version 2.1 requirements will be met:
http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
02110-1301 USA
'''

#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Test cases for Abstract class'''

import sys
import unittest

from sample import Abstract

class Incomplete(Abstract):
    def __init__(self):
        Abstract.__init__(self)

class Concrete(Abstract):
    def __init__(self):
        Abstract.__init__(self)
        self.pure_virtual_called = False
        self.unpure_virtual_called = False

    def pureVirtual(self):
        self.pure_virtual_called = True

    def unpureVirtual(self):
        self.unpure_virtual_called = True


class AbstractTest(unittest.TestCase):
    '''Test case for Abstract class'''

    def testAbstractPureVirtualMethodAvailability(self):
        '''Test if Abstract class pure virtual method was properly wrapped.'''
        self.assert_('pureVirtual' in dir(Abstract))

    def testAbstractInstanciation(self):
        '''Test if instanciation of an abstract class raises the correct exception.'''
        self.assertRaises(NotImplementedError, Abstract)

    def testUnimplementedPureVirtualMethodCall(self):
        '''Test if calling a pure virtual method raises the correct exception.'''
        i = Incomplete()
        self.assertRaises(NotImplementedError, i.pureVirtual)

    def testReimplementedVirtualMethodCall(self):
        '''Test if instanciation of an abstract class raises the correct exception.'''
        i = Concrete()
        self.assertRaises(NotImplementedError, i.callPureVirtual)

    def testReimplementedVirtualMethodCall(self):
        '''Test if a Python override of a virtual method is correctly called from C++.'''
        c = Concrete()
        c.callUnpureVirtual()
        self.assert_(c.unpure_virtual_called)

    def testImplementedPureVirtualMethodCall(self):
        '''Test if a Python override of a pure virtual method is correctly called from C++.'''
        c = Concrete()
        c.callPureVirtual()
        self.assert_(c.pure_virtual_called)

if __name__ == '__main__':
    unittest.main()

