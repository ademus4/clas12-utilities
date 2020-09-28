#!/usr/bin/env python
import mysql.connector
import time
import sys

MAX_ROWS = 5e4

path_prefix='/volatile/clas12'
if len(sys.argv)>1:
  path_prefix=sys.argv[1]

now = time.strftime('%c')
datetime = str(now)

db = mysql.connector.connect(
  host="scidbw.jlab.org",
  user="dummy",
  passwd="",
  database="wdm"
)

cursor = db.cursor()
cursor.execute('select reserved, cached/1024./1024./1024. from projectDisk where root = "%s"'%path_prefix)

result_limits = cursor.fetchall()
line_array = result_limits[0]
reserved = float(line_array[0])
used = float(line_array[1])
target_size = used - reserved
if target_size < 1000.0:
  target_size = 1000.0
#if target_size > 10000.0:
#  target_size = 10000.0

dirlist = []
def checkdir(dir):
  if dir not in dirlist:
    dirlist.append(dir)
    return True
  else:
    return False

title = path_prefix+':  Auto-Deletion Queue'

print('<html>')
print('<head><title>' + title + '</title></head>')
print('<body>')
print('<h1>' + title + '</h1>')
print('<p> Last Updated: ' + datetime + '</p>')
print('<table border>')
print('<tr>')
print('<th>running directory count</th>')
print('<th>running file count</th>')
print('<th>running sum of <br/> size of old files (GB)</th>')
print('<th>file mod time</th>')
print('<th>file owner</th>')
print('<th>directories with oldest files</th>')
print('<th>oldest file in directory</th>')
print('</tr>')

query = 'select vfile.mod_time as mtime, file_name, vfile.owner, size, full_path '
query+= 'from vfile, vdirectory, projectDisk '
query+= 'where vfile.dir_index = vdirectory.dir_index '
query+= 'and projectDisk.disk_index = vdirectory.disk_index '
query+=' and root = "%s" '%path_prefix
query+=' order by mtime'

#cursor.execute('select vfile.mod_time as mtime, file_name, vfile.owner, size, full_path from vfile, vdirectory, projectDisk where vfile.dir_index = vdirectory.dir_index and projectDisk.disk_index = vdirectory.disk_index and root = "/volatile/clas12" order by mtime')
cursor.execute(query)

result = cursor.fetchall()

count = 0
count_dir = 0
sum = float(0);
for i in range(len(result)):
  count += 1
  line_array = result[i]
  sum += float(line_array[3])
  sum_gb = sum/1024.0/1024.0/1024.0
  dir = str(line_array[4])
  if checkdir(dir):
    count_dir += 1
    line_str_array = []
    for j in range(len(line_array)):
      line_str_array.append(str(line_array[j]))
    line = '<tr>'
    line += '<td>%d</td>'%count_dir
    line += '<td>%d</td>'%count
    line += '<td>%.3f</td>'%sum_gb
    line += '<td>%s</td>'%line_str_array[0]
    line += '<td>%s</td>'%line_str_array[2]
    line += '<td>%s</td>'%line_str_array[4].replace(path_prefix+'/','')
    line += '<td>%s</td>'%line_str_array[1]
    line += '</tr>'
    print(line)
  if sum_gb > target_size or count_dir > MAX_ROWS:
    break

print('</table>')
print('</body>')
print('</html>')


