allDatas = [];

for i= 1:10
    data = readtable('arm_commands.csv', 'Delimiter', ',');
    data.timestamp = seconds(data.timestamp);
    dataT = array2timetable(data.command, 'RowTimes',data.timestamp)
    
    dataArr = table2array(data(:,2));
    dataLast = round(dataArr(end),2)
    allDatas = [allDatas, dataLast];
    pause(1.0)
end

disp(allDatas(end-3:end))