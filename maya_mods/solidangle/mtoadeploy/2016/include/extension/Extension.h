#pragma once

#include "translators/NodeTranslator.h"
#include "utils/Version.h"

#include <maya/MTypeId.h>
#include <maya/MPxNode.h>

#include <algorithm>

#define EXPORT_API_VERSION DLLEXPORT const char* getAPIVersion(){return MTOA_VERSION;}

#define PLUGIN_SEARCH "$ARNOLD_PLUGIN_PATH"
#define EXTENSION_SEARCH "$MTOA_EXTENSIONS_PATH"

#ifdef WIN32
#define PATH_SEPARATOR ";"
#else
#define PATH_SEPARATOR ":"
#endif

// callback functions to create new translators
typedef void *   (*TCreatorFunction)();
typedef void     (*TNodeInitFunction)(CAbTranslator);

class CExtensionImpl;

// class CExtension

/// Class to represent and manipulate Arnold extensions.
///
/// This class is used in the initializeExtensions and deinitializeExtension functions
/// of a MtoA extension to respectively register and deregister the extension services
/// (nodes, translators) with MtoA and Maya.RT CExtension
///


class DLLEXPORT CExtension
{
   friend class CExtensionsManager;

public:
   CExtension(const MString &file);
   virtual ~CExtension() {}
   void Requires(const MString &plugin);
   MStringArray Required();
   MString GetExtensionName() const;
   MString GetExtensionFile() const;
   MString GetApiVersion() const;
   unsigned int RegisteredNodesCount() const;
   unsigned int TranslatedNodesCount() const;
   unsigned int TranslatorCount() const;
   bool IsRegistered() const;
   bool IsDeferred() const;

   // Arnold Plugin loading
   MString LoadArnoldPlugin(const MString &file,
                            const MString &path=PLUGIN_SEARCH,
                            MStatus *returnStatus=NULL);
   // Get list of Arnold plugins this extension loads
   MStringArray GetOwnLoadedArnoldPlugins();

   // Can be called directly to register new Maya nodes
   MStatus RegisterNode(const MString &mayaTypeName,
                        const MTypeId &mayaTypeId,
                        MCreatorFunction creatorFunction,
                        MInitializeFunction initFunction,
                        MPxNode::Type type=MPxNode::kDependNode,
                        const MString &classification="");

   // To register a translator for a given Maya node
   // gives no access to metadata (all info needs to be set explicitely)
   MStatus RegisterTranslator(const MString &mayaTypeName,
                              const MString &translatorName,
                              TCreatorFunction creatorFunction,
                              TNodeInitFunction nodeInitFunction=NULL);

   // Register Maya nodes for all Arnold nodes declared with
   // the given plugin, using metadata info
   MStatus RegisterPluginNodesAndTranslators(const MString &plugin="");

   MStatus RegisterAOV(const MString &nodeType,
                       const MString &aovName,
                       int dataType,
                       const MString &aovAttr);

   static bool IsArnoldPluginLoaded(const MString &path);
   static MStringArray GetAllLoadedArnoldPlugins();



protected:
   CExtensionImpl *m_impl;
};
