/**
 * @file drv_key.c
 * @brief 按键驱动模块
 * @author
 * @date 2026-05-16
 */
#include "drv_key.h"

/**
 * @brief 初始化按键 GPIO
 */
void KEY_Init(void)
{
    GPIO_InitTypeDef GPIO_Initure;


    GPIO_Initure.Pin = KEY1_Pin;
    GPIO_Initure.Mode = GPIO_MODE_INPUT;
    GPIO_Initure.Pull = GPIO_PULLUP;
    GPIO_Initure.Speed = GPIO_SPEED_HIGH;
    HAL_GPIO_Init(KEY1_GPIO_Port, &GPIO_Initure);

    GPIO_Initure.Pin = KEY2_Pin;
    GPIO_Initure.Mode = GPIO_MODE_INPUT;
    GPIO_Initure.Pull = GPIO_PULLUP;
    GPIO_Initure.Speed = GPIO_SPEED_HIGH;
    HAL_GPIO_Init(KEY2_GPIO_Port, &GPIO_Initure);

    GPIO_Initure.Pin = KEY3_Pin;
    GPIO_Initure.Mode = GPIO_MODE_INPUT;
    GPIO_Initure.Pull = GPIO_PULLUP;
    GPIO_Initure.Speed = GPIO_SPEED_HIGH;
    HAL_GPIO_Init(KEY3_GPIO_Port, &GPIO_Initure);

    GPIO_Initure.Pin = KEY4_Pin;
    GPIO_Initure.Mode = GPIO_MODE_INPUT;
    GPIO_Initure.Pull = GPIO_PULLUP;
    GPIO_Initure.Speed = GPIO_SPEED_HIGH;
    HAL_GPIO_Init(KEY4_GPIO_Port, &GPIO_Initure);



}
