#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "nrf_soc.h"
#include "nrf_nvic.h"

#include "bootloader_utils.h"

#define RESTART_APP         0xC5
#define START_BOOTLOADER    0xB2

static const uint8_t bootloader_key[] =
{
    0x6d, 0x4e, 0xa4, 0x45, 0xe8, 0xf4, 0x4c, 0x10,
    0xbb, 0x9a, 0xb5, 0x24, 0xbd, 0x51, 0x45, 0x9c
};

//static const uint8_t bootloader_key[] = { 0xA5 };

#define KEY_LEN (sizeof(bootloader_key))

uint8_t bootloader_utils_get_key_len(void)
{
    return KEY_LEN;
}

bool bootloader_utils_match_key(uint8_t * const p_key, uint8_t length)
{
    if(length != KEY_LEN)
    {
        return false;
    }

    if(memcmp(p_key, bootloader_key, KEY_LEN) == 0)
    {
        return true;
    }
    return false;
}

void bootloader_utils_reset_app(void)
{
#if (NRF_SD_BLE_API_VERSION==3)
    sd_power_gpregret_set(0, RESTART_APP);
#else
    sd_power_gpregret_set(RESTART_APP);
#endif

    sd_nvic_SystemReset();
}

void bootloader_utils_start_bl(void)
{
#if (NRF_SD_BLE_API_VERSION==3)
    sd_power_gpregret_set(0, START_BOOTLOADER);
#else
    sd_power_gpregret_set(START_BOOTLOADER);
#endif
    
    sd_nvic_SystemReset();
}
