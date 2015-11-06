#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################
# Name    : infoSetExp
# Version : 001
# Description : Export to a file les coordonnées des global et local SRT des set d'une scene
# Author : Jean-Philippe Descoins
# Date : 2014-04-01
# Comment : WIP
################################################################
#    ! Toute utilisation de ce se script sans autorisation     #
#                         est interdite !                      #
#    ! All use of this script without authorization is         #
#                           forbidden !                        #
#                                                              #
#                                                              #
#                 © Jean-Philippe Descoins                     #
################################################################







import maya.cmds as cmds
import os
import dminutes.jipeLib_Z2K as jpZ
reload(jpZ)
jpZ.infosFromMayaScene()


#################### infoSet Export file creation
# get all set reference

# get namespace

# construct output dict


# get private path

# write the file

# publish the file