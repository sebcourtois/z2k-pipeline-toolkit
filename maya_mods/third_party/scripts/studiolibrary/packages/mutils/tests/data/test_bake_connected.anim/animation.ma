//Maya ASCII 2016 scene
//Name: animation.ma
//Last modified: Mon, Mar 21, 2016 10:00:44 AM
//Codeset: 1252
requires maya "2016";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2016";
fileInfo "version" "2016";
fileInfo "cutIdentifier" "201502261600-953408";
fileInfo "osv" "Microsoft Windows 8 Business Edition, 64-bit  (Build 9200)\n";
createNode animCurveTU -n "CURVE1";
	rename -uid "18787E0C-46AC-E82F-9311-F483C13BE593";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 10;
createNode animCurveTU -n "CURVE2";
	rename -uid "C91144C3-4AF8-AD37-EF73-91929E7EBE27";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 10 ".ktv[0:9]"  1 8 2 8 3 8 4 8 5 8 6 8 7 8 8 8 9 8 10 8;
	setAttr -s 10 ".kit[9]"  1;
	setAttr -s 10 ".kot[0:9]"  1 18 18 18 18 18 18 18 
		18 18;
	setAttr -s 10 ".kix[9]"  1;
	setAttr -s 10 ".kiy[9]"  0;
	setAttr -s 10 ".kox[0:9]"  1 1 1 1 1 1 1 1 1 1;
	setAttr -s 10 ".koy[0:9]"  0 0 0 0 0 0 0 0 0 0;
// End