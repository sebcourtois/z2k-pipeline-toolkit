#pragma once

#include "translators/DagTranslator.h"
#include <maya/MFnCamera.h>

const double MM_TO_INCH = 0.03937;

enum FitType
{
   FIT_FILL = 0,
   FIT_BEST,
   FIT_HORIZONTAL,
   FIT_VERTICAL,
   FIT_TOSIZE,
};

/** \class CCameraTranslator
 A Translator class that exports Maya Camera nodes

 \see CDagTranslator
*/

class DLLEXPORT CCameraTranslator
   :   public CDagTranslator
{
public:

// ---- Virtual functions derived from CNodeTranslator
   virtual void Init();
   virtual bool RequiresMotionData();
   
protected:
   virtual void GetMatrix(AtMatrix& matrix);
   virtual void RequestUpdate();
   virtual void NodeChanged(MObject& node, MPlug& plug); 

//-----------------

   double GetDeviceAspect();
   void SetFilmTransform(AtNode* camera, double factorX=0, double factorY=0, double width=0, bool persp=true);
   void ExportImagePlanes();
   void ExportDOF(AtNode* camera);
   void ExportCameraData(AtNode* camera);

   static void MakeDefaultAttributes(CExtensionAttrHelper &helper);
   static void MakeDOFAttributes(CExtensionAttrHelper &helper);

protected:
   MFnCamera m_fnCamera;
};
