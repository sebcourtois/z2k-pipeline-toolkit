#pragma once

#include "common/UnorderedContainer.h"
#include <maya/MObject.h>
#include <maya/MDagPath.h>
#include <maya/MAnimControl.h>
#include <maya/MStringArray.h>
#include <maya/MString.h>
#include <maya/MVector.h>

/// Specify the Session mode for current export
enum ArnoldSessionMode
{
   MTOA_SESSION_UNDEFINED = 0,  ///< Unknown
   MTOA_SESSION_RENDER = 1, ///< Render in Maya Render View
   MTOA_SESSION_BATCH, ///< Batch Render
   MTOA_SESSION_IPR,  ///< IPR Rendering in Maya Render View
   MTOA_SESSION_SWATCH, ///< Simple rendering performed for the swatches (e.g. Attribute Editor)
   MTOA_SESSION_ASS, ///< Exporting the scene to .ASS file
   MTOA_SESSION_AIR,  
   MTOA_SESSION_RENDERVIEW, ///< Render with Arnold RenderView
   MTOA_SESSION_MATERIALVIEW, ///< Material Viewer rendering
   MTOA_SESSION_SEQUENCE,  ///< Render a Sequence from Maya interface
   MTOA_SESSION_ANY
};

/// Determines the Light-linking rules for this export
enum ArnoldLightLinkMode
{
   MTOA_LIGHTLINK_NONE,  ///< Ignore Light-linking
   MTOA_LIGHTLINK_MAYA ///<  Follow Maya's Light linking
};

///< Determines the Shadow Linking rules for this export
enum ArnoldShadowLinkMode
{
   MTOA_SHADOWLINK_NONE, ///< Ignore Shadow linking
   MTOA_SHADOWLINK_LIGHT, ///< Follow same rules as light-linking
   MTOA_SHADOWLINK_MAYA, ///< Follow Maya's shadow linking
};

// Filters
#define MTOA_FILTER_DISABLE   0x0000
#define MTOA_FILTER_HIDDEN    0x0001
#define MTOA_FILTER_TEMPLATED 0x0002
#define MTOA_FILTER_LAYER     0x0004
#define MTOA_FILTER_ANY       0xFFFF

typedef unordered_set<MFn::Type, hash<int> > MFnTypeSet;

struct CMayaExportFilter
{
   unsigned int state_mask;
   MFnTypeSet excluded;

   CMayaExportFilter() :  state_mask(MTOA_FILTER_ANY) {}
};

#define MTOA_MBLUR_DISABLE 0x0000
#define MTOA_MBLUR_LIGHT   0x0001
#define MTOA_MBLUR_CAMERA  0x0002
#define MTOA_MBLUR_OBJECT  0x0004
#define MTOA_MBLUR_DEFORM  0x0008
#define MTOA_MBLUR_SHADER  0x0010
#define MTOA_MBLUR_ANY     0xFFFF

#define MTOA_MBLUR_TYPE_START    0x0000
#define MTOA_MBLUR_TYPE_CENTER   0x0001
#define MTOA_MBLUR_TYPE_END      0x0002
#define MTOA_MBLUR_TYPE_CUSTOM   0x0003

struct CMotionBlurOptions
{
   unsigned int   enable_mask;
   unsigned int   steps;
   unsigned int   range_type;
   double         motion_frames;
   double         motion_start;
   double         motion_end;

   CMotionBlurOptions() :  enable_mask(MTOA_MBLUR_DISABLE),
                           steps(1),
                           range_type(MTOA_MBLUR_TYPE_CENTER),
                           motion_frames(0.0),
                           motion_start(-0.25),
                           motion_end(0.25) {}
};

/// Structure to hold options relative to a CArnoldSession
struct CSessionOptions
{
   friend class CArnoldSession;
   friend class CMayaScene;


   // --- Getters
   inline const ArnoldSessionMode& GetSessionMode() const {return m_mode;}
   inline const ArnoldLightLinkMode& GetLightLinkMode() const {return m_lightlink;}
   inline const ArnoldShadowLinkMode& GetShadowLinkMode() const {return m_shadowlink;}
   inline const MDagPath& GetExportCamera() const { return m_camera; }
   inline const CMayaExportFilter& GetExportFilter() const { return m_filter; }
   inline unsigned int GetExportFilterMask() const { return m_filter.state_mask; }
   inline bool IsMotionBlurEnabled(int type = MTOA_MBLUR_ANY) const { return (m_motion.enable_mask & type) != 0; }
   inline unsigned int GetRangeType() const {return m_motion.range_type;}
   inline unsigned int GetNumMotionSteps() const { return m_motion.steps; }
   inline double GetExportFrame() const { return m_frame; }
   inline double GetMotionByFrame() const { return m_motion.motion_frames; }
   inline bool IsProgressive() const { return m_progressiveRendering; }
   inline double GetScaleFactor() const { return m_scaleFactor; }
   inline MVector GetOrigin() const { return m_origin; }
   const MStringArray &GetTextureSearchPaths() const {return m_textureSearchPaths;}
   const MStringArray &GetProceduralSearchPaths() const {return m_proceduralSearchPaths;}
   inline bool GetExportFullPath() const {return m_exportFullPath;}
   inline const MString &GetExportPrefix() const {return m_exportPrefix;}

   // if I don't inline this here, some contrib libs fail at linking
   inline void GetMotionRange(double &motion_start, double &motion_end) const {
      switch (m_motion.range_type)
      {
         case MTOA_MBLUR_TYPE_START:
            motion_start = 0.;
            motion_end = m_motion.motion_frames;
            break;
         case MTOA_MBLUR_TYPE_CENTER:
            motion_start = -0.5 * m_motion.motion_frames;
            motion_end = 0.5 * m_motion.motion_frames;
            break;
         case MTOA_MBLUR_TYPE_END:
            motion_start = -m_motion.motion_frames;
            motion_end = 0.;
            break;
         default:
         case MTOA_MBLUR_TYPE_CUSTOM:
            motion_start = m_motion.motion_start;
            motion_end = m_motion.motion_end;
            break;
      }
   }

   inline const MObject& GetArnoldRenderOptions() const { return m_options; }
   void FormatTexturePath(MString& texturePath) const
   {
      ReplaceSlashes(texturePath);
      if (!m_absoluteTexturePaths)
      {
         // if the filename starts with one of the texture search paths, remove the path from the filename
         for (unsigned int i = 0; i < m_textureSearchPaths.length(); ++i)
         {
            const MString& currentSearchPath = m_textureSearchPaths[i];
            if (texturePath.indexW(currentSearchPath) == 0)
            {
               texturePath = texturePath.substringW(currentSearchPath.length(), texturePath.length());
               break;
            }
         }
      }
      // convert to UTF-8
      texturePath = texturePath.asUTF8();
   }

   void FormatProceduralPath(MString& proceduralPath) const
   {
      ReplaceSlashes(proceduralPath);
      if (!m_absoluteProceduralPaths)
      {
         for (unsigned int i = 0; i < m_proceduralSearchPaths.length(); ++i)
         {
            const MString& currentSearchPath = m_proceduralSearchPaths[i];
            if (proceduralPath.indexW(currentSearchPath) == 0)
            {
               proceduralPath = proceduralPath.substringW(currentSearchPath.length(), proceduralPath.length());
               break;
            }
         }
      }
      // convert to UTF-8
      proceduralPath = proceduralPath.asUTF8();
   }

   bool IsBatch() const { return (GetSessionMode() == MTOA_SESSION_BATCH || GetSessionMode() == MTOA_SESSION_ASS); }
   bool IsInteractiveRender() const {return (GetSessionMode() == MTOA_SESSION_RENDERVIEW || GetSessionMode() == MTOA_SESSION_IPR); }

private:

   CSessionOptions() :  m_options(MObject()),
                        m_camera(MDagPath()),
                        m_textureSearchPaths(),
                        m_exportPrefix(""),
                        m_filter(CMayaExportFilter()),
                        m_motion(CMotionBlurOptions()),
                        m_origin(0.0, 0.0, 0.0),
                        m_frame(0.0),
                        m_scaleFactor(1.0),
                        m_mode(MTOA_SESSION_UNDEFINED),
                        m_lightlink(MTOA_LIGHTLINK_NONE),
                        m_shadowlink(MTOA_SHADOWLINK_NONE),                        
                        m_progressiveRendering(false),
                        m_absoluteTexturePaths(true),
                        m_absoluteProceduralPaths(true),
                        m_exportFullPath(false)
                        
   {
      m_frame = MAnimControl::currentTime().as(MTime::uiUnit());
   }

   // Setters : private as this is not meant to be modified

   inline void SetSessionMode(ArnoldSessionMode mode) { m_mode = mode; }
   inline void SetLightLinkMode(ArnoldLightLinkMode mode) { m_lightlink = mode; }
   inline void SetShadowLinkMode(ArnoldShadowLinkMode mode) { m_shadowlink = mode; }
   inline void SetExportCamera(MDagPath camera) { camera.extendToShape();m_camera = camera; }
   inline void SetExportFilterMask(unsigned int mask) { m_filter.state_mask = mask; }
   inline void SetArnoldRenderOptions(const MObject& options) { m_options = options; }
   inline void SetExportFrame(double frame) { m_frame = frame; }
   inline void SetProgressive(const bool is_progressive) { m_progressiveRendering = is_progressive; }

   inline void SetExportFullPath(bool b) {m_exportFullPath = b;}
   inline void SetExportPrefix(const MString &prefix) {m_exportPrefix = prefix;}

   MStatus GetFromMaya();


   static void ReplaceSlashes(MString& str, bool isDir = false)
   {
   #ifdef _WIN32
      MStringArray tmp;
      str.split('\\', tmp);
      if (tmp.length() > 1)
      {
         str = tmp[0];
         for (unsigned int i = 1; i < tmp.length(); ++i)
         {
            str += "/";
            str += tmp[i];
         }
      }
   #endif
      if (isDir && (str.length() > 1) && (str.substring(str.length() - 1, str.length() - 1) != "/"))
         str += "/";
   }

   
private:

   MObject              m_options;
   MDagPath             m_camera;
   MStringArray         m_textureSearchPaths;
   MStringArray         m_proceduralSearchPaths;
   MString              m_exportPrefix;

   CMayaExportFilter    m_filter;
   CMotionBlurOptions   m_motion;

   MVector              m_origin;

   double               m_frame;
   double               m_scaleFactor;

   ArnoldSessionMode    m_mode;
   ArnoldLightLinkMode  m_lightlink;
   ArnoldShadowLinkMode m_shadowlink;

   bool                 m_progressiveRendering;
   bool                 m_absoluteTexturePaths;
   bool                 m_absoluteProceduralPaths;
   bool                 m_exportFullPath;
};
