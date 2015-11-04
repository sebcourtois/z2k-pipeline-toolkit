# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary/packages/mutils\tests\__init__.py
"""
# Released subject to the BSD License
# Please visit http://www.voidspace.org.uk/python/license.shtml
#
# Copyright (c) 2014, Kurt Rathjen
# All rights reserved.
# Comments, suggestions and bug reports are welcome.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
   # * Redistributions of source code must retain the above copyright
   #   notice, this list of conditions and the following disclaimer.
   # * Redistributions in binary form must reproduce the above copyright
   # notice, this list of conditions and the following disclaimer in the
   # documentation and/or other materials provided with the distribution.
   # * Neither the name of Kurt Rathjen nor the
   # objects of its contributors may be used to endorse or promote products
   # derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY KURT RATHJEN  ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL KURT RATHJEN BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# Example:
# RUN TEST SUITE
import mutils.tests
reload(mutils.tests)
mutils.tests.run()
"""
import unittest
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(funcName)s: %(message)s', filemode='w')

def suite():
    """
    :rtype: unittest.TestSuite
    """
    import test_pose
    import test_anim
    import test_match
    suite_ = unittest.TestSuite()
    suite_.addTest(test_match.TestMatch('test_match1'))
    suite_.addTest(test_match.TestMatch('test_match2'))
    suite_.addTest(test_match.TestMatch('test_match3'))
    suite_.addTest(test_match.TestMatch('test_match4'))
    suite_.addTest(test_match.TestMatch('test_match5'))
    suite_.addTest(test_match.TestMatch('test_match6'))
    suite_.addTest(test_match.TestMatch('test_match7'))
    suite_.addTest(test_match.TestMatch('test_match8'))
    suite_.addTest(test_match.TestMatch('test_match9'))
    suite_.addTest(test_match.TestMatch('test_match10'))
    suite_.addTest(test_match.TestMatch('test_match11'))
    suite_.addTest(test_match.TestMatch('test_match12'))
    suite_.addTest(test_match.TestMatch('test_match13'))
    suite_.addTest(test_match.TestMatch('test_match14'))
    suite_.addTest(test_match.TestMatch('test_match15'))
    suite_.addTest(test_match.TestMatch('test_match16'))
    suite_.addTest(test_match.TestMatch('test_match17'))
    suite_.addTest(test_pose.TestPose('test_save'))
    suite_.addTest(test_pose.TestPose('test_load'))
    suite_.addTest(test_pose.TestPose('test_blend'))
    suite_.addTest(test_pose.TestPose('test_select'))
    suite_.addTest(test_pose.TestPose('test_older_version'))
    suite_.addTest(test_anim.TestAnim('test_load_insert'))
    suite_.addTest(test_anim.TestAnim('test_older_version'))
    suite_.addTest(test_anim.TestAnim('test_load_replace'))
    suite_.addTest(test_anim.TestAnim('test_bake_connected'))
    suite_.addTest(test_anim.TestAnim('test_load_replace_completely'))
    return suite_


def run():
    """
    """
    tests = unittest.TextTestRunner()
    tests.run(suite())