#pragma once

#include "NodeTranslator.h"

/** \class CDagTranslator
 * Abstract base class for Dag node translators.

 \see CNodeTranslator
 \see CShapeTranslator
 \see CLightTranslator
*/

class DLLEXPORT CDagTranslator : public CNodeTranslator
{

public:

//------- Virtual methods inherited from CNodeTranslator

   /// Initialize the translator
   virtual void Init();

   /// Customize the callbacks invoked during IPR updates for DAG nodes
   virtual void AddUpdateCallbacks();

protected:
   CDagTranslator() : CNodeTranslator(){}

   /// Export (convert from Maya to Arnold) this node
   virtual void Export(AtNode* atNode);

   /// Export for motion steps
   virtual void ExportMotion(AtNode* atNode);

//-----------------------------------------

public:

   /// Returns the maya DAG path of the node associated to this translator
   const MDagPath &GetMayaDagPath() const { return m_dagPath; }

   /// Returns true if this DAG node is meant to be rendered (or false it's hidden, etc...). It can eventually be overridden
   virtual bool IsRenderable() const;

   // Create Maya visibility attributes with standardized render flag names
   // These are the attributes that compute the "visibility" parameter. there are other
   // attributes like self_shadow and opaque that are computed separately

   /// This is for custom DAG nodes where none of the standard maya visibility attributes
   /// are available. typically CDagTranslator::AddArnoldVisibilityAttrs() is the appropriate function.
   static void MakeMayaVisibilityFlags(CBaseAttrHelper& helper);
   
   /// Arnold's visibiltity mask adds several relationships not available by default in Maya.
   /// use in conjunction with CDagTranslator::ComputeVisibility() or CShapeTranslator::ProcessRenderFlags().
   static void MakeArnoldVisibilityFlags(CBaseAttrHelper& helper);

   /// Static function to force the export of a specific MDagPath and get the generated translator.
   static CDagTranslator *ExportDagPath(const MDagPath &dagPath);

   /// Returns true if this is one of the translate/rotate/scale parameters
   static bool IsTransformPlug(const MPlug &plug);

   /// Returns the arnold name for a corresponding maya dag path
   static MString GetArnoldNaming(const MDagPath &dagPath);

   /// If this function returns false, children of this dag node won't be exported
   virtual bool ExportDagChildren() const {return true;}

protected:

   /** Export the matrix at current step
   This is a utility method which handles the common tasks associated with
   exporting matrix information. It properly handles exporting a matrix array
   if motion blur is enabled and required by the node. it should be called
   at each motion step
   */
   void ExportMatrix(AtNode* node);

   /** Return whether the current dag object is the master instance.
   
    The master is the first instance that is completely visible (including parent transforms)
    for which full geometry should be exported.
   
    Always returns true if this dagPath is not instanced.
    If dagPath is instanced, this searches the preceding instances
    for the first that is visible. if none are found, dagPath is considered the master.
   
    This function caches the result on the first run and returns the cached results on
    subsequent calls.
   
    note: dagPath is assumed to be visible.
   
    @return                  whether or not dagPath is a master
   \see GetMasterInstance
   */
   bool IsMasterInstance();

   /** Return the DAG path of the master instance.
    The master is the first instance that is completely visible (including parent transforms)
    for which full geometry should be exported.
    \see IsMasterInstance
    */
   MDagPath& GetMasterInstance();

   /// Use standardized render flag names to return an arnold visibility mask
   AtByte ComputeVisibility();

   /// Compute the Arnold Matrix for current node.  Can be overridden if necessary
   virtual void GetMatrix(AtMatrix& matrix);
   
   /// Maya Dag path of this maya object
   MDagPath m_dagPath;

private:
   /// Internal use only
   virtual void CreateImplementation();
};
