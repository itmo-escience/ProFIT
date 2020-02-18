from ProcessMap import ProcessMap

SOURCE_PATH = 'C:/Users/L-Elh/Desktop/DEV/'
SOURCE_FILE = 'log_data'
OUTPUT_PATH = 'C:/Users/L-Elh/Desktop/DEV/'
OUTPUT_FILE = 'process_map'
  
pm = ProcessMap()
print(pm.get_log(), pm.get_rates(), pm.get_params())
print(pm.get_T(), pm.get_graph(), pm.render_map())
pm.set_log(SOURCE_PATH + SOURCE_FILE + '.csv', encoding='cp1251')
pm.set_rates(100, 0)
pm.set_params(False, False)
print(pm.get_log(), pm.get_rates(), pm.get_params())
print(pm.get_T(), pm.get_graph(), pm.render_map())
pm.update()
print(pm.get_log(), pm.get_rates(), pm.get_params())
print(pm.get_T(), pm.get_graph(), pm.render_map())
pm.set_params(True, False)
pm.update()
print(pm.get_log(), pm.get_rates(), pm.get_params())
print(pm.get_T(), pm.get_graph(), pm.render_map())
GV = pm.render_map()
GV.save(OUTPUT_PATH+OUTPUT_FILE)