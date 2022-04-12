/****************************************************************************
**
** Copyright (C) 2022 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the test suite of Qt for Python.
**
** $QT_BEGIN_LICENSE:GPL-EXCEPT$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3 as published by the Free Software
** Foundation with exceptions as appearing in the file LICENSE.GPL3-EXCEPT
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#ifndef STDSHAREDPTRTESTBENCH_H
#define STDSHAREDPTRTESTBENCH_H

#include "libsmartmacros.h"

#include <memory>

class Integer;

class LIB_SMART_API StdSharedPtrTestBench
{
public:
    StdSharedPtrTestBench();
    ~StdSharedPtrTestBench();

    static std::shared_ptr<Integer> createInteger(int v = 42);
    static std::shared_ptr<Integer> createNullInteger();
    static void printInteger(const std::shared_ptr<Integer> &);

    static std::shared_ptr<int> createInt(int v = 42);
    static std::shared_ptr<int> createNullInt();
    static void printInt(const std::shared_ptr<int> &);
};

#endif // STDSHAREDPTRTESTBENCH_H
