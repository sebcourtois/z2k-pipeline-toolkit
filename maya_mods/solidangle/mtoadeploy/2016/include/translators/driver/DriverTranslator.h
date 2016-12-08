#pragma once

#include "translators/NodeTranslator.h"

//--------------- DriverTranslator ------------------------------------------

class DLLEXPORT CDriverTranslator
   :  public CNodeTranslator
{
public:
   static void* creator()
   {
      return new CDriverTranslator();
   }
   static void NodeInitializer(CAbTranslator context);
   AtNode* CreateArnoldNodes();
   void Export(AtNode* atNode);

protected:
   virtual void AddUpdateCallbacks();
};
