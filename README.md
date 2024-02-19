# xiaomi_miio_toilet
小米马桶/马桶圈插件 
 
不再维护，请使用miot插件代替（已完善miot冲水功能，需要等该request合并）  
https://github.com/al-one/hass-xiaomi-miot/pull/1480

目前此插件已支持以下设备类型：
* 小鲸洗中支持米家app的马桶/马桶圈
* 其它接入米家app的马桶/马桶圈没有设备未测试

目前支持获取的状态：
1. 是否着坐（默认的state）
2. 是否开启马桶圈加热
3. 是否开启夜灯

目前支持操作：
1. 冲马桶（马桶圈不支持）
2. 开关马桶圈加热
3. 开关夜灯
## 安装

* 将 custom_component 文件夹中的内容拷贝至自己的相应目录

或者
* 将此 repo ([https://github.com/nesror/xiaomi_miio_toilet](https://github.com/nesror/xiaomi_miio_toilet)) 添加到 [HACS](https://hacs.xyz/)，然后添加“Xiaomi Miio Toilet”

## 配置
```
binary_sensor:
  - platform: xiaomi_miio_toilet
    name: my_toilet
    host: xxx
    token: xxx
    scan_interval: 10
```

## 服务
* 冲马桶（马桶圈不支持）
```
service: xiaomi_miio_toilet.flush_on
  data:
    entity_id: binary_sensor.my_toilet
```
* 开关马桶圈加热：1开，0关
```
service: xiaomi_miio_toilet.work_seatheat
  data:
    entity_id: binary_sensor.my_toilet
    status: 1
```
* 开关夜灯：1开，0关
```
service: xiaomi_miio_toilet.work_night_led
  data:
    entity_id: binary_sensor.my_toilet
    status: 1
```
