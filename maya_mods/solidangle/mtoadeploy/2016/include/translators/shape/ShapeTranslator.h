#pragma once

#include "translators/DagTranslator.h"
#include <maya/MPlugArray.h>

/** \class CShapeTranslator
 * Base class for shape translators. To export custom geometries to Arnold, one must derive 
   from this class.

 \see CNodeTranslator
 \see CShapeTranslator
 \see CLightTranslator
*/

class DLLEXPORT CShapeTranslator : public CDagTranslator
{
public:

   //--- Virtual function derived from CNodeTranslator

   /// Initialize the Shape Translator
   virtual void Init();
   /// Specify whether this shape requires motion, based on global motion blur options
   virtual bool RequiresMotionData();

   /// Customize the update callbacks to add shader assignments
   virtual void AddUpdateCallbacks();
   
   /// Export the shaders assigned to this shape (via shading groups).
   /// Do not invoke it if RequiresShaderExport returns false
   virtual void ExportShaders(){}

protected:

   /// Computes and sets the visibility mask as well as other shape attributes related to ray visibility (self_shadows, opaque)
   virtual void ProcessRenderFlags(AtNode* node);

   /** Export the trace sets for this given MPlug. 
    Note that ProcessRenderFlags will invoke this method with MPlug "aiTraceSets".
    It is therefore useless to invoke it if ProcessRenderFlags is already used
    \see ProcessRenderFlags
    */
   static void ExportTraceSets(AtNode* node, const MPlug& traceSetsPlug);

   /// Export the light linking for the current Maya Object
   void ExportLightLinking(AtNode* polymesh);
   
   /// For initializer callbacks : Create attributes common to arnold shape nodes
   static void MakeCommonAttributes(CBaseAttrHelper& helper);
      
   /** Set an already created shader as the root shader for this shape.
    This is used when the shader is created manually. The return value contains the
    shading engine that has to be linked to the "shader" param of the shape.
    Do not invoke it if RequiresShaderExport returns false
    \see RequiresShaderExport
    */
   void SetRootShader(AtNode *rootShader);


   /// Returns the Maya MPlug for the shading group attribute on the given MObject
   static MPlug GetNodeShadingGroup(MObject dagNode, int instanceNum);

   /// Returns true if the Shader Export is enabled in the Global Options.
   /// Don't call ExportShaders if this method returns false
   static bool RequiresShaderExport();
protected:
   bool m_motion;
   bool m_motionDeform;
};
