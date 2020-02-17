from ProcessMap import ProcessMap

SOURCE_PATH = 'C:/Users/L-Elh/Desktop/DEV/'
SOURCE_FILE = 'log_data'
OUTPUT_PATH = 'C:/Users/L-Elh/Desktop/DEV/'
OUTPUT_FILE = 'process_map'
  
pm = ProcessMap()
pm.set_log(SOURCE_PATH + SOURCE_FILE + '.csv', encoding='cp1251')
pm.set_rates(100, 0)
pm.set_params(False, False)
pm.update()
pm.set_params(True, False)
pm.update()
GV = pm.render_map()
GV.save(OUTPUT_PATH+OUTPUT_FILE)