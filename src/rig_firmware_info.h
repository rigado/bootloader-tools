/** @file rig_firmware_info.c
*
* @brief This module creates and stores, in the ROM image, information
*        about the firmware image.
*
* @par
* COPYRIGHT NOTICE: (c) Rigado
* All rights reserved. 
*
* Source code licensed under Software License Agreement in license.txt.
* You should have received a copy with purchase of BMD series product 
* and with this repository.  If not, contact modules@rigado.com.
*/

#ifndef _RIG_FIRMWARE_INFO_H_
#define _RIG_FIRMWARE_INFO_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
    
typedef enum version_type_e
{
    VERSION_TYPE_RELEASE = 1,
    VERSION_TYPE_DEBUG
} version_type_t;

typedef enum softdevice_support_e
{
    SOFTDEVICE_SUPPORT_S110 = 1,
    SOFTDEVICE_SUPPORT_S120,
    SOFTDEVICE_SUPPORT_S130,
    SOFTDEVICE_SUPPORT_S132,
    SOFTDEVICE_SUPPORT_S332,
    SOFTDEVICE_SUPPORT_RESERVED3,
    SOFTDEVICE_SUPPORT_RESERVED4,
    SOFTDEVICE_SUPPORT_RESERVED5
} softdevice_support_t;

typedef enum hardware_support_e
{
    HARDWARE_SUPPORT_NRF51 = 1,
    HARDWARE_SUPPORT_NRF52,
    HARDWARE_SUPPORT_RESERVED1,
    HARDWARE_SUPPORT_RESERVED2,
    HARDWARE_SUPPORT_RESERVED3,
    HARDWARE_SUPPORT_RESERVED4,
    HARDWARE_SUPPORT_RESERVED5
} hardware_support_t;

typedef __packed struct rig_firmware_info_s
{
    uint32_t magic_number_a;        /**< Always 0x465325D4*/
    uint32_t size;                  /**< Size of this structure*/
    uint8_t version_major;          /**< Printable major version number*/
    uint8_t version_minor;          /**< Printable minor version number*/
    uint8_t version_rev;            /**< Printable revision number*/
    uint32_t build_number;          /**< Number corresponding to actual version of firwmare*/
    version_type_t version_type;    /**< Release or Debug*/
    softdevice_support_t sd_support;/**< Supported SoftDevice*/
    hardware_support_t hw_support;  /**< Supported hardware type*/
    uint16_t protocol_version;      /**< Protocol version for this bootloader*/
    uint32_t magic_number_b;        /**< Always 0x49B0784C*/
} rig_firmware_info_t;

#ifdef __cplusplus
}
#endif

#endif
