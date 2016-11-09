require runtime;
require system;

module: shotgun_fields_config_standard
{

require shotgun_stringMap;
StringMap := shotgun_stringMap.StringMap;

function: serverMap (string; )
{
    /* -----------------------------------------*/
    return "";

    /* -----------------------------------------*/
    // ONLY IF YOU WANT TO USE OLD SCRIPT_KEY-BASED AUTHENTICATION: Insert your
    // Shotgun server url followed by a space followed by the Application Key
    // for the 'rv' Script on that server. You can add additional servers if
    // you like by appending them to the string with a space. Ex: "server1_url
    // application_key1 server2_url application_key2"

}

    /* -----------------------------------------*/
    // FOR THE DEFAULT CONFIGURATION NO OTHER FIELDS SHOULD BE MODIFIED BELOW HERE
    /* -----------------------------------------*/

function: fieldDescriptors((string, string, string, string, string, bool)[]; )
{
    (string, string, string, string, string, bool)[] descriptors = {

    /* -----------------------------------------*/
    // REQUIRED
    /* -----------------------------------------*/
    // name                 prettyName              fieldName               fieldType       entityType      compute
    ("id",                  "ID",                   "id",                   "number",       "Version",      false),

    /* -----------------------------------------*/
    // ENTITY FIELDS
    /* -----------------------------------------*/
    // name                 prettyName              fieldName               fieldType       entityType      compute
    ("link",                "Link",                 "entity",               "entity",       "Version",      false),
    ("shot",                "Shot",                 "link",                 "entity",       "Version",      true),
    ("asset",               "Asset",                "link",                 "entity",       "Version",      true),
    ("sequence",            "Sequence",             "sg_sequence",          "entity",       "Shot",         false),
    ("project",             "Project",              "project",              "entity",       "Version",      false),
    ("task",                "Task",                 "sg_task",              "entity",       "Version",      false),
    ("user",                "Artist",               "user",                 "entity",       "Version",      false),
    ("humanUser",           "HumanUser",            "user",                 "entity",       "Version",      false),

    /* -----------------------------------------*/
    // MEDIA TYPES
    /* -----------------------------------------*/
    // name                 prettyName              fieldName                       fieldType       entityType      compute
    ("mt_Movie",            "Path To Movie",        "sg_path_to_movie",             "text",         "Version",      false),
    ("mt_Movie_aspect",     "Movie Aspect Ratio",   "sg_movie_aspect_ratio",        "float",        "Version",      false),
    ("mt_Movie_hasSlate",   "Movie Has Slate",      "sg_movie_has_slate",           "checkbox",     "Version",      false),
                                                                                                            
    ("mt_Frames",           "Path To Frames",       "sg_path_to_frames",            "text",         "Version",      false),
    ("mt_Frames_aspect",    "Frames Aspect Ratio",  "sg_frames_aspect_ratio",       "float",        "Version",      false),
    ("mt_Frames_hasSlate",  "Frames Have Slate",    "sg_frames_have_slate",         "checkbox",     "Version",      false),

    /* -----------------------------------------*/
    // EDITORIAL INFO
    /* -----------------------------------------*/
    // name                 prettyName              fieldName               fieldType      entityType       compute
    ("frameMin",            "First Frame",          "sg_first_frame",       "number",      "Version",       false),
    ("frameMax",            "Last Frame",           "sg_last_frame",        "number",      "Version",       false),
    ("frameIn",             "In Frame",             "sg_cut_in",   		"number",      "Shot",          false),
    ("frameOut",            "Out Frame",            "sg_cut_out",  		"number",      "Shot",          false),
    ("cutOrder",            "Cut Order",            "sg_cut_order",         "number",      "Shot",          false),

    /* -----------------------------------------*/
    // ADDITIONAL FIELDS
    /* -----------------------------------------*/
    // name                 prettyName              fieldName               fieldType       entityType      compute
    ("name",                "Name",                 "code",                 "text",         "Version",      false),
    ("description",         "Description",          "description",          "text",         "Version",      false),
    ("created",             "Created",              "created_at",           "date_time",    "Version",      false),
    ("status",              "Status",               "sg_status_list",       "status_list",  "Version",      false),
    ("shotStatus",          "Shot Status",          "sg_status_list",       "status_list",  "Shot",         false),
    ("assetStatus",         "Asset Status",         "sg_status_list",       "status_list",  "Asset",        false),
    ("department",          "Department",           "sg_department",        "text",         "Version",      false),
    ("flagged",             "Flagged",              "flagged",              "checkbox",     "Version",      false)
    };

    return descriptors;
};

function: actualCutOrder (int; string cutOrderValue)
{
    return int(cutOrderValue);
}

function: displayOrder (string[]; )
{
    string[] fo = string [] {
        "id",
        "name",
        "description",
        "department",
        "status",
        "user",
        "created",
        "shot",
        "shotStatus",
        "asset",
        "assetStatus",
        "mt_Movie",
        "mt_Frames"
    };
}

function: fieldsCompute (void; StringMap data, bool incremental)
{
    if (incremental) return;
    
    /* -----------------------------------------*/
    // DEFAULT ASPECT RATIO IS 0.0 IF NONE IS SET, sets to "Get aspect ratio from file"
    /* -----------------------------------------*/
    if (data.find("mt_Movie_aspect") eq nil) data.add("mt_Movie_aspect", "0.0"); 
    if (data.find("mt_Frames_aspect") eq nil) data.add("mt_Frames_aspect", "0.0"); 
    
	let sShotPath = system.getenv("ZOMB_SHOT_PATH", nil);
    if (sShotPath neq nil)
    {
		sShotPath = regex.replace("\\\\", sShotPath, "/");
		//print(sShotPath+"\n");
		//print("******************2\n");
		let frames = data.find("mt_Frames"),
			movie = data.find("mt_Movie");

		if (frames neq nil && regex.match("^\$ZOMB_SHOT_PATH", frames))
		{
			//print("$ZOMB_SHOT_PATH found in frames path\n");
			frames = regex.replace("^\$ZOMB_SHOT_PATH", frames, sShotPath);
			data.add("mt_Frames", frames);
		}
		if (movie neq nil && regex.match("^\$ZOMB_SHOT_PATH", movie))
		{
			//print("$ZOMB_SHOT_PATH found in movies path\n");
			movie = regex.replace("^\$ZOMB_SHOT_PATH", movie, sShotPath);
			data.add("mt_Movie", movie);
		}
	}
    /* -----------------------------------------*/
    // DEBUGGING
    /* -----------------------------------------*/
    //print("***************************************\n");
    //print("%s" % data.toString());
    //print("***************************************\n");
}

}
