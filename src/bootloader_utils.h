/** @file bootloader_utils.h
*
* @brief This module creates and stores, in the ROM image, information
*        about the firmware image.
*
* @par
* COPYRIGHT NOTICE: (c) Rigado
* All rights reserved. 
*/
#ifndef BOOTLOADER_UTILS_H_
#define BOOTLOADER_UTILS_H_

#include <stdint.h>
#include <stdbool.h>

uint8_t bootloader_utils_get_key_len(void);
bool bootloader_utils_match_key(uint8_t * const p_key, uint8_t length);
void bootloader_utils_reset_app(void);
void bootloader_utils_start_bl(void);

#endif //BOOTLOADER_UTILS_H_
