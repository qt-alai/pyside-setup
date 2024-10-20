# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only WITH Qt-GPL-exception-1.0
from __future__ import annotations

import os
import sys
import unittest

from pathlib import Path
sys.path.append(os.fspath(Path(__file__).resolve().parents[1]))
from init_paths import init_test_paths
init_test_paths(False)

from helper.usesqapplication import UsesQApplication

from PySide6.QtWidgets import QDoubleSpinBox, QGraphicsBlurEffect


class TestSignalConnection(UsesQApplication):
    def testFloatSignal(self):
        foo1 = QDoubleSpinBox()
        foo2 = QDoubleSpinBox()
        foo1.valueChanged[float].connect(foo2.setValue)
        foo2.valueChanged[float].connect(foo1.setValue)
        foo1.setValue(0.42)
        self.assertEqual(foo1.value(), foo2.value())

    def testQRealSignal(self):
        foo1 = QDoubleSpinBox()
        effect = QGraphicsBlurEffect()
        effect.blurRadiusChanged['qreal'].connect(foo1.setValue)  # check if qreal is a valid type
        effect.setBlurRadius(0.42)
        self.assertAlmostEqual(foo1.value(), effect.blurRadius())


if __name__ == '__main__':
    unittest.main()
