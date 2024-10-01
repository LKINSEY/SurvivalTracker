dirs =  uipickfiles(); 
mice = cellfun(@(x) x(end-5:end), dirs, 'UniformOutput', false);
scanDates = cellfun(@(x) {dir(fullfile(x,'*-*')).name}, dirs, 'UniformOutput', false);
mouseInfo = struct();
forTiffs = struct();
for mix = 1:length(mice)
  mousePath = dirs{mix};
  measurements = scanDates{mix};
  numScans = {};
  for date = 1:length(measurements) %redundant i know...
        %first for loop, iterate through scans and get length of max scans
        scanPath = [mousePath filesep measurements{date} filesep 'scans' ];     
        scanFNs = ls(scanPath); scanFNs = cellstr(scanFNs(3:end, :));
        numScans{date} = length(scanFNs);
  end
  maxScans = max(cell2mat(numScans));
  scanIndex = num2cell(NaN(maxScans,length(measurements)));
  size(scanIndex)
  for date = 1:length(measurements)
      %do this again but its fast so its ok
        sizeOfScans = size(scanIndex,1);
        scanPath = [mousePath filesep measurements{date} filesep 'scans' ];     
        scanFNs = ls(scanPath); scanFNs = cellstr(scanFNs(3:end, :));
        scanFNs =  scanFNs(strncmp(scanFNs, 'scan', 4));
        % csvPath = [dir(fullfile([mousePath filesep measurements{date}], '*scan info*')).folder filesep dir(fullfile([mousePath filesep measurements{date}], 'scan info*')).name];
        %for the GFP only below
        csvPath = [ mousePath filesep measurements{date} filesep dir(fullfile([mousePath filesep measurements{date}], 'scan_info*')).name];
        csvData = readtable(csvPath);
        roiID = cellfun(@(x) str2double(x(2:end)), csvData.scanfieldROI, 'UniformOutput', false);
        extractNumber = @(str) regexp(str, '^\d+', 'match', 'once'); % Function to extract the number from the string or return empty if not applicable
        measurementIDX = cell2mat(cellfun(@(x) str2double(extractNumber(x)), csvData.scan__power, 'UniformOutput', false));
        

        boundariesOfScans = ~isnan(measurementIDX);
        if length(boundariesOfScans) < sizeOfScans
            boundariesOfScans(length(boundariesOfScans)+1:sizeOfScans) = 0; %this shows us where to plug ordered items
        else
            boundariesOfScans = boundariesOfScans(1:sizeOfScans);
        end
        orderROIsScanned = scanFNs(measurementIDX(~isnan(measurementIDX)));
        insertIndices = find(boundariesOfScans);
        for i = 1:length(scanFNs)
            scanIndex(insertIndices(i),date) = join([mousePath filesep measurements{date} filesep 'scans' filesep orderROIsScanned(i)],'');
        end
        

  end
  scanIndex

  %inefficiently find the NaNs and kill em
  roisToStudy = zeros(size(scanIndex,1),1);


  if size(scanIndex,2) == 4
      disp('CHECK')
    for i = 1:size(scanIndex,1)
            if any(  ~cell2mat(cellfun(@(x) ischar(x), scanIndex(i,1:3), 'UniformOutput', 0))     )
                roisToStudy(i) = 0;
            else
                roisToStudy(i) = 1;
                alignMeasures(scanIndex(i,1:3), mousePath, i)
            end
    end

  else
    for i = 1:size(scanIndex,1)
            if any(  ~cell2mat(cellfun(@(x) ischar(x), scanIndex(i,:), 'UniformOutput', 0))     )
                roisToStudy(i) = 0;
            else
                roisToStudy(i) = 1;
                alignMeasures(scanIndex(i,:), mousePath, i)
            end
    end
  end
  

  mousePath(end-6:end)
  roisToStudy

end


