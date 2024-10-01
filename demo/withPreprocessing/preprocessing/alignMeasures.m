function alignMeasures(dirs, savePath, roiName)
    exptSummaryArr = cellfun(@(x) [dir(fullfile(x, '*EXPTSUMMARY.mat')).folder filesep dir(fullfile(x, '*EXPTSUMMARY.mat')).name], dirs, 'UniformOutput', false);
    
    meanIMs = {}; actIMs ={}; imageSizes = {};
    for i = 1:length(exptSummaryArr) % for every exp file we look at
        %get all your file info
        exptSummary = load(exptSummaryArr{i}).exptSummary;
        thisFile = split(exptSummaryArr{i},'\');
        thisScan = thisFile{end};
        thisPath = join(thisFile(1:end-2),'\');
        thisScanInfo = split(thisScan, '_'); saveDate = join(thisScanInfo{end-2});
    
        %Get image and load it correctly
        extractedMean = exptSummary.meanIM; extractedAct = exptSummary.actIM;
        correctedMean = normalizeLocal(extractedMean, 21, 0.9, false);
        extractedAct = extractedAct./prctile(extractedAct(~isnan(extractedAct)),99);
        extractedAct = extractedAct - prctile(extractedAct(~isnan(extractedAct)), 66);
        correctedAct = normalizeLocal(extractedAct, 21, 1);
        meanIM = imrotate(correctedMean, 90); actIM = imrotate(correctedAct, 90);
        imageSizes{i} = size(meanIM);
        meanIMs{i} = meanIM; actIMs{i} = actIM;
    
        maxSize = max(cat(1,imageSizes{:}));
    end
    finalStack_struct = zeros(maxSize(1), maxSize(2), length(exptSummaryArr));
    finalStack_act = zeros(maxSize(1), maxSize(2), length(exptSummaryArr));
    for i = 1:length(exptSummaryArr)
        paddedImg_struct = padarray(meanIMs{i}, maxSize - size(meanIMs{i}), 0, 'post');
        paddedImg_act = padarray(actIMs{i}, maxSize - size(meanIMs{i}), 0, 'post');
        finalStack_struct(:,:,i) = paddedImg_struct;
        finalStack_act(:,:,i) = paddedImg_act;
    end
    
    %Anatomical Info
    alignedMeasures_struct = straightenMeasurement(finalStack_struct);
    
    %Activity Info
    % alignedMeasures_act = straightenMeasurement(finalStack_act);
    
    % %sanity check!!! Works!!! Im sane!!!!
    % figure; imshow3D(alignedMeasures_struct)
    % figure; imshow3D(alignedMeasures_act)
    
    %save as tiff stack
    filename = join([savePath filesep 'roiNum' string(roiName) '.tif'],'');
    imwrite(alignedMeasures_struct(:,:,1), filename, 'TIFF', 'Compression', 'none');
    for z = 2:size(alignedMeasures_struct, 3)
        imwrite(alignedMeasures_struct(:,:,z), filename, 'TIFF', 'WriteMode', 'append', 'Compression','none');
    end
end


function IMout= straightenMeasurement(IM)
maxShift = 16;
Y = makeHighPass(IM); % data order is XYCZ
Z2fft = fft2(Y(:,:,1));
IMout = IM;
dX = 0; dY = 0;
for Z1 = 1:(size(IM, 3)-1) %made 4 a 3 because grayscale
    Z1fft = Z2fft;
    Z2fft = fft2(Y(:,:,Z1+1));
    output = dftregistration_clipped(Z1fft,Z2fft,4,maxShift);
    dX = dX + output(4);
    dY = dY+output(3);
    IM(isnan(IM)) = 0; %so imtranslate doesn't bugout
    IMout(:,:,Z1+1) = imtranslate(IM(:,:,Z1+1), [dX dY]);
end
end