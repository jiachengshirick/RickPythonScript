def copperCounter(initial_copper_number):
    #初始购买正铜量
    initial_Copper = initial_copper_number

    #废品率和转换率
    scrap_rate = 0.5
    conversion_ratio = 1

    #实际消耗正铜量
    actual_consumed_copper = 0

    #废铜可以换取的正铜量
    while initial_Copper >= 1:
        #计算废铜
        scrap_copper = initial_Copper * scrap_rate
        #换取的正铜
        exchanged_copper = scrap_copper * conversion_ratio
        #累加
        actual_consumed_copper += exchanged_copper
        #更新
        initial_Copper = exchanged_copper
    return int(actual_consumed_copper)

initial_copper = 200
copper_count = copperCounter(initial_copper)
# copper_count = 100
heng = copper_count*3500/1.13+initial_copper*(49000/1.13)
print("当初始正铜吨数为：" + str(initial_copper) + "吨时，废铜吨数为：" + str(copper_count) + "吨。" )
print("横山桥消耗：" + str(heng))
zhejiang = copper_count*(-43600+49000/1.13)+initial_copper*(49000/1.13)
print("浙江消耗：" + str(zhejiang))

print("每吨废铜上的消耗差为：" + str((heng-zhejiang)/copper_count))