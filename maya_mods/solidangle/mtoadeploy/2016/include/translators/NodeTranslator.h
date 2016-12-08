#pragma once


#include "platform/Platform.h"
#include "attributes/AttrHelper.h"
#include "session/SessionOptions.h"
#include "extension/AbTranslator.h"

#include <ai_nodes.h>
#include <ai_ray.h>
#include <ai_universe.h>

#include <maya/MDagPath.h>
#include <maya/MFnDagNode.h>
#include <maya/MPlug.h>
#include <maya/MGlobal.h>
#include <maya/MMessage.h> // for MCallbackId
#include <maya/MCallbackIdArray.h>
#include <maya/MNodeMessage.h>

#include <string>
#include <vector>
#include <map>

class CNodeTranslatorImpl;
class CArnoldSession;
struct CSessionOptions;

/** \class CNodeTranslator
 *
 *  \brief Translators are used to convert a given Maya node into one or several Arnold nodes. They are invoked during .ASS Export, Render, IPR, etc... 
 *  To create an extension for a specific kind of maya node, one should derive a Translator from the appropriate type. CShapeTranslator should be used for custom 
 *  geometries, CLightTranslator for lights, CDagTranslator for other DAG nodes, CShaderTranslator for shaders, etc...
 *  The most important function to derive is Export(AtNode *node) in order to convert Maya data into Arnold data, but several other functions are useful for specific purpose.
 *  \see CDagTranslator
 *  \see CShapeTranslator
 *  \see CShaderTranslator
 *  \see CLightTranslator
 *  \see CSessionOptions
  */
class DLLEXPORT CNodeTranslator
{
   friend class CArnoldSession;
   friend class CExtensionsManager;
   friend class CExtension;
   friend class CExtensionImpl;
   friend class CRenderSwatchGenerator;
   friend class CMaterialView;
   friend class CNodeTranslatorImpl;

protected:

//--------------------------------------
//------- Virtual methods, to be derived if necessary

   /** Initialize the Translator

     This function can be derived in order to initialize data in the translator. At this point the information about the input Maya node is already valid.
     Init is called just before CreateArnoldNodes    
    \see CreateArnoldNodes
   */
   virtual void Init() {}

   /** Function invoked to create the Arnold nodes for this translator

      By deriving this function, one should create the Arnold AtNode for this translator, by exclusively calling AddArnoldNode.
      If multiple nodes have to be created by this translator, they don't necessarily have to be created in this function. 
      It's however important than the main AtNode is created (and returned) here. 
     This function is invoked right after Init .
    \see AddArnoldNode
    \see ProcessAOVOutput
    \see Init
   */
   virtual AtNode* CreateArnoldNodes() = 0;

   /** Convert the input Maya node to the Arnold world

     This function is invoked for any kind of session (IPR, Render, Batch, .ass Export, Swatch, Material View, etc...), and should be derived by new Translators to convert a Maya node into Arnold data.
     When Motion Blur is enabled, this function is invoked for the current frame, then ExportMotion is invoked for the motion steps. Animated arrays should be allocated
     here and filled at the step index returned by GetMotionStep . The other array steps will be filled in ExportMotion. In order to know if this is a 'first' export
     or an IPR "update" one can invoke IsExported
    \param[in]  node   Output Arnold node to be filled. This is the main Arnold node as returned by GetArnoldNode and is provided as argument for convenience
    \see ExportMotion
   */
   virtual void Export(AtNode* node);

   /** Export the motion steps for this node

      When motion blur is enabled, Export will be called once for the "current" frame and then ExportMotion will be called for each motion step.
      If specific animated parameters have to be exported at each motion step, this should be done in this function. The current motion step
      can be obtained by GetMotionStep  and its total amount is returned by GetNumMotionSteps. Note that this function will *only* be called if 
      RequiresMotionData returns true.
    \param[in]  node   Output Arnold node to be filled. This is the main Arnold node as returned by GetArnoldNode and is provided as argument for convenience
    \see Export
    \see RequiresMotionData
    \see GetMotionStep
    \see GetNumMotionSteps
   */
   virtual void ExportMotion(AtNode* node) {};

public:
   /** Determine if this node requires motion data

      When motion blur is enabled, Export will be called once for the "current" frame and then ExportMotion will be called for each motion step.
      However, the latest is only called if RequiresMotionData returns true. Otherwise, only Export will be called as MtoA will consider that 
      this node is *not* motion blurred. By deriving this function, one can determine that behaviour.
    \see AddArnoldNode
    \see ProcessAOVOutput
    \see Init
   */
   virtual bool RequiresMotionData() {return false;}


   /** Customize what happens when a Maya attribute changes during IPR

      During IPR, any change in a Maya node can cause the render to refresh. To customize this update behaviour in a translator, 
      one must derive NodeChanged and apply different actions depending on which plug attribute was changed.
    \note If a translator doesn't call its parent class function NodeChanged, then no refresh will occur at all.
    \param[in]  node   Maya Object causing this function to be called
    \param[in]  plug   Maya Attribute (plug) that receives a "dirtiness" signal from Maya, meaning that either itself or its connections are being modified
    \see RequestUpdate
    \see SetUpdateMode
   */
   virtual void NodeChanged(MObject& node, MPlug& plug); 

   /** Function invoked by NodeChanged to request an IPR update for this node.
    To be eventually derived to define custom behaviour
    \see NodeChanged
    \see SetUpdateMode
    */
   virtual void RequestUpdate();

protected:
   /** Add specific IPR update callbacks for this Translator

      During IPR, any change in a Maya node can cause the render to refresh. To add specific Maya callbacks in order to refresh the render properly,
      one can derive AddUpdateCallbacks and register specific callbacks. Each of these callbacks should be register by calling RegisterUpdateCallback
      in order to be properly cleared when necessary.
    \see RegisterUpdateCallback
   */
   virtual void AddUpdateCallbacks();

   /// Delete the Arnold node(s) for this translator.
   virtual void Delete();

   /// If the translator needs to performs different operations depending on the type of output plug, it should derive this method and return true
   virtual bool DependsOnOutputPlug() {return false;} 


//----------------------------------------------------------------------------------
//------- Non-virtual methods, meant to be invoked by translators
protected:

   /** Function used to create an Arnold node for this translator
   
    Arnold nodes should never be created "manually" by invoking Arnold function AiNode() in translators.
    Instead they should be created by invoking this function, that will keep track of the created nodes
    and will clear them when necessary. When a translator creates multiple Arnold nodes, they have to be created with 
    a specific tag , that is used as a key to identify each of them.

    \param[in] type   Type of the arnold node to create
    \param[in] tag    When multiple nodes are created, a tag can be used as a key to identify a specific node
    \see CreateArnoldNodes
    \see ProcessAOVOutput
    */
   AtNode* AddArnoldNode(const char* type, const char* tag=NULL);

   /** Register an update callback created in AddUpdateCallbacks

     Every callback created in AddUpdateCallbacks should be register using this function, 
     in order to be cleared when necessary
     \param[in] id   MCallbackId  of the callback to be registered
     \see AddUpdateCallbacks
   */   
   void RegisterUpdateCallback(const MCallbackId id);

public:

   /// Get the MObject associated to this translator
   MObject GetMayaObject() const;

   /** Retrieve a node previously created using AddArnoldNode()
    In case multiple Arnold nodes are registered for this translator, returns the one for a given tag (key)
    param[in] tag  Eventually specify a tag to identify an Arnold node belonging to this translator in case of multiple arnold nodes
    */
   AtNode* GetArnoldNode(const char* tag=NULL);

   /// Returns true if this translator has already been exported before. It can be useful to know if an export is
   /// actually an IPR update
   bool IsExported() const;

   /** Returns true if we are exporting the motion (i.e. changing the current frame). While exporting motion, the function
    ExportMotion will be invoked for all translators for whom RequiresMotionData is true
    \see ExportMotion
    \see RequiresMotionData
    */
   bool IsExportingMotion() const;

   /// Defines how a Translator will be processed at next IPR update
   enum UpdateMode {
      AI_UPDATE_ONLY=0, ///< Simple update. Export will be called and IsExported will return true
      AI_RECREATE_NODE = 1, ///< Delete the arnold node(s) and re-export from scratch. IsExported will return false at next Export
      AI_RECREATE_TRANSLATOR, ///< Delete the translator and re-generate one. 
      AI_DELETE_NODE   ///< Delete the node and the translator
   };
   /** Specify an UpdateMode for next IPR update.
        
        This function is usually invoked from NodeChanged or RequestUpdate to specify how 
        a translator is updated at each IPR refresh
        \param[in] mode  UpdateMode defining how this translator will be updated
        \see UpdateMode
        \see NodeChanged
        \see RequestUpdate
   */
   void SetUpdateMode(UpdateMode mode);

    /** Get the the Maya plug for this given attribute name.
      This function can be used (e.g. during Export ) to get the Maya Plug attribute from given name,
      taking overrides into account.

      \see ProcessParameter
      \see Export
      \note Attributes can be automatically converted based on their type using ProcessParameter

   */
   MPlug FindMayaPlug(const MString &attrName, MStatus* ReturnStatus=NULL) const;

  
   /**  Helper to convert a given Arnold attribute from the Maya object automatically, based on its type
      
      By default, no maya attribute name is provided and it is searched by default based on arnoldParamName
      \param[in] arnoldNode  Arnold node on which the parameter must be set
      \param[in] arnoldParamName  Name of the arnold parameter to be converted.
      \param[in] arnoldParamType  Type of the Arnold parameter (AI_TYPE_FLOAT, AI_TYPE_RGB, etc...)
      \param[in] mayaAttrName  Optionally specify a name for the Maya Attribute. If not specified, an 'ai' prefix will be added to arnoldParamName
      \see ProcessArrayParameter
      \see Export      
   */

   AtNode* ProcessParameter(AtNode* arnoldNode, const char* arnoldParamName, int arnoldParamType, MString mayaAttrName  = "");
   
   /** Helper to convert a given Arnold attribute from the Maya attribute (plug) automatically based on its type
   \param[in] arnoldNode  Arnold node on which the parameter must be set
   \param[in] arnoldParamName  Name of the arnold parameter to be converted.
   \param[in] arnoldParamType  Type of the Arnold parameter (AI_TYPE_FLOAT, AI_TYPE_RGB, etc...)
   \param[in] plug  Maya attribute to be used for the maya-to-arnold conversion
   \see ProcessParameter
   \see ProcessArrayParameter
   \see Export
   */
   AtNode* ProcessParameter(AtNode* arnoldNode, const char* arnoldParamName, int arnoldParamType, const MPlug& plug);

   /** Helper to convert a given Arnold array attribute automatically

      Convert the given array attribute (allocating the AtArray). By default, no param Type is provided and it is determined automatically. 
      A child array MObject can be provided optionally

   \param[in] arnoldNode  Arnold node on which the parameter must be set
   \param[in] arnoldParamName  Name of the arnold parameter to be converted.
   \param[in] plug  Maya array attribute to be used for the maya-to-arnold conversion
   \param[in] arnoldParamType  Optional : Type of the Arnold parameter (AI_TYPE_FLOAT, AI_TYPE_RGB, etc...)
   \param[in] childArray  Optional : To be used when the Maya MPlug has several MObject childs
   
   \see ProcessParameter
   \see ProcessArrayParameter
   \see Export
   */
   void ProcessArrayParameter(AtNode* arnoldNode, const char* arnoldParamName, const MPlug& plug, unsigned int arnoldParamType = AI_TYPE_UNDEFINED, MObject *childArray = NULL);

   /** Export (and eventually create) the arnold node connected to a given attribute.
      When a Maya plug has a connection to another node, it is necessary to call ExportConnectedNode to export 
      the connected maya node to Arnold
      \param[in] outputPlug  Maya attribute plug which connected node has to be exported
      \note This function allows to create all of the shading tree shaders, from the root shader to the leafs
   */
   AtNode* ExportConnectedNode(const MPlug& outputPlug);

   /** Get the current Motion step being exported (when motion blur is enabled for this node).
      When Motion Blur is enabled, ExportMotion will be called for each motion step. 
      This method will return the current step being exported, and should be used to determine the index to be filled in AtArrays.
   \note During first Export , when an AtArray is being allocated, it shouldn't be filled with index 0 anymore, but with index = GetMotionStep
   \see GetNumMotionSteps
   \see ExportMotion
   */
   unsigned int GetMotionStep();

   /// Get the Amount of Motion steps if motion blur is enabled for this node (return 1 otherwise).
   unsigned int GetNumMotionSteps();

   /// Returns the value of the "motionBlur" flag on this Maya object
   bool IsLocalMotionBlurEnabled() const;

   /// Get the name of the Maya object. 
   MString GetMayaNodeName() const;
   /// Get the name of this translator
   MString GetTranslatorName();
   /// For multi-output translators, get the name of the output attribute in maya
   MString GetMayaOutputAttributeName() const;


//---------------------------------------------------
// -------- Static functions

   // Static method set as a "creator" callback for the translator
   static void NodeInitializer(CAbTranslator context);

   /// Get the global CSessionOptions of the current scene.
   static const CSessionOptions& GetSessionOptions();

   /// Convert a matrix from Maya to Arnold data
   static void ConvertMatrix(AtMatrix& matrix, const MMatrix& mayaMatrix);
   
   /// Get the Arnold name corresponding to a Maya object. For Dag nodes, prefer the function in CDagTranslator with a MDagPath argument
   static MString GetArnoldNaming(const MObject &object);

   // Request an update of the TX textures generation
   static void RequestTxUpdate();
   /// Request an update of light links in the scene
   static void RequestLightLinksUpdate();

   /// Get the MtoA Translator associated to a Maya object in the scene
   static CNodeTranslator *GetTranslator(const MObject &object);
   /// Get the MtoA Translator associated to a Maya DAG node in the scene
   static CNodeTranslator *GetTranslator(const MDagPath &dagPath);
      
   /// Callback used to be adverted of changes in the scene. Can be used in AddUpdateCallbacks when the parent function isn't called.
   static void NodeDirtyCallback(MObject& node, MPlug& plug, void* clientData);
   /// Callback used to be adverted of object's name modifications. Can be used in AddUpdateCallbacks when the parent function isn't called.
   static void NameChangedCallback(MObject& node, const MString& str, void* clientData);
   /// Callback used to be adverted when nodes are deleted in the scene. Can be used in AddUpdateCallbacks when the parent function isn't called.
   static void NodeAboutToBeDeletedCallback(MObject& node, MDGModifier& modifier, void* clientData);

   /// Export the MObject user attributes to the given Arnold node. This is only needed when the target AtNode is different than GetArnoldNode()
   static void ExportUserAttributes(AtNode* anode, MObject object, CNodeTranslator* translator = 0);

//-----------------------------------------
//------ Shortcuts to get information from the global CSessionOptions

   /// Get the frame being exported
   static double GetExportFrame();
   /// Get the status of global motion blur for a specific motion type
   static bool IsMotionBlurEnabled(int type = MTOA_MBLUR_ANY);
   /// Get the ArnoldSessionMode of current export (IPR, Render, Batch, .ASS Export, etc...)
   static ArnoldSessionMode GetSessionMode();
   /// Get the Maya Object containing the Arnold global options
   static const MObject& GetArnoldRenderOptions();
   /// Get the shutter length for motion blur
   static double GetMotionByFrame();
   /// Get the list of motion steps that being processed by current export
   static const double *GetMotionFrames(unsigned int &count);


/// Class destructor
   virtual ~CNodeTranslator();
   
protected:
   /** Protected Constructor

     Translators should never be created manually, this is done by the MtoA export.
     At this point, no data is present about the Maya input node. In order to initialize data
     related to Maya nodes, one should derive Init()
    \see Init
   */
   CNodeTranslator();

   /// Internal use only
   CNodeTranslatorImpl * m_impl;
private:
   /// Internal use only
   virtual void CreateImplementation();

};
