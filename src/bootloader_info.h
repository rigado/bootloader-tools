/** @file bootloader_info.c
*
* @brief This module provides functions to retrieve the installed bootloader
*        version information.
*
* @par
* COPYRIGHT NOTICE: (c) Rigado
* All rights reserved. 
*
* Source code licensed under Software License Agreement in license.txt.
* You should have received a copy with purchase of BMD series product 
* and with this repository.  If not, contact modules@rigado.com.
*/

#ifndef _BOOTLOADER_INFO_H_
#define _BOOTLOADER_INFO_H_

#include <stdint.h>
#include "rig_firmware_info.h"

#ifdef __cplusplus 
extern “C” { 
#endif

/**@brief Read bootloader version information
 *
 * @pre p_info points at valid memory
 * @post Bootloader version info copied to p_info
 *
 * @param[in] p_info Storage pointer for the version structure
 *
 * @retval ::NRF_SUCCESS The metric data was changed
 * @retval ::NRF_ERROR_INVALID_PARAM Input pointer is null
 * @retval ::NRF_ERROR_INVALID_DATA The version data is invalid meaning this bootloader version does not 
 *           have this information available.
 */
uint32_t bootloader_info_read(rig_firmware_info_t * p_info);

#ifdef __cplusplus 
}
#endif

#endif
