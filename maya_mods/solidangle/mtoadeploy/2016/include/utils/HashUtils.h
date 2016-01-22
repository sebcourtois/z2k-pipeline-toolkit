#pragma once

#include <ai.h>

inline int getHash(AtNode* node)
{
   return (int)AiNodeGetStr(node, AtString("name")).hash();
}
