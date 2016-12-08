#pragma once

#include "translators/DagTranslator.h"

class DLLEXPORT CLightTranslator
   :   public CDagTranslator
{

/** \class CLightTranslator
 A Translator class that exports Maya Light nodes

 \see CDagTranslator
*/
public:
   virtual bool RequiresMotionData();
protected:
   virtual void Export(AtNode* light);
   virtual void ExportMotion(AtNode* light);
   virtual void NodeChanged(MObject& node, MPlug& plug);

//--------

   /// Infinite / Directional lights must return false. This determines if scaling is taken into account
   virtual bool IsFinite() const { return true; } 

   /// static function that adds the attributes that are common to all Lights in arnold
   static void MakeCommonAttributes(CBaseAttrHelper& helper);


public:
   /// handles the color temperature conversion to RGB
   static AtRGB ConvertKelvinToRGB(float kelvin);
};
