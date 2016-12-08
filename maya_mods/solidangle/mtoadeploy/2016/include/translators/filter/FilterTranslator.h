#pragma once

#include "translators/NodeTranslator.h"

//--------------- FilterTranslator ------------------------------------------

class DLLEXPORT CFilterTranslator
   :  public CNodeTranslator
{
public:
   static void* creator()
   {
      return new CFilterTranslator();
   }
   static void NodeInitializer(CAbTranslator context);
   AtNode* CreateArnoldNodes();
   void Export(AtNode* atNode);

protected:
   virtual void AddUpdateCallbacks();
};
