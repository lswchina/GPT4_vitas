
d = {}
with open('2022_us_1.csv') as f:
    s = f.read()
    s_line = s.split('\n')

    for i in s_line:
        s_line_divided =  i.split(",")
        d[s_line_divided[0]] = s_line_divided

# use d to quick loop up by O(1) e.g.d['B09PLN23BZ']







