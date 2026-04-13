step=11;
%Results directory
folder_name = '/local/ModelData/ISMIP6Results/Antarctic2300';

%Scaling map for area correction and sectors
scale_file =['/local/ModelData/ISMIP6Data/Processing/af2_el_ismip6_ant_01.nc'];
scalefac = double(ncread(scale_file,'af2'));
sectors_32km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_32km.nc'],'sectors'); %18 sectors at 32 km resolution
regions_32km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_32km.nc'],'regions'); %3 regions (West, East and Peninsula)
sectors_16km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_16km.nc'],'sectors'); %18 sectors at 16 km resolution
regions_16km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_16km.nc'],'regions'); %3 regions (West, East and Peninsula)
sectors_8km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_8km.nc'],'sectors'); %18 sectors at 8 km resolution 
regions_8km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_8km.nc'],'regions'); %3 regions (West, East and Peninsula)
sectors_4km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_4km.nc'],'sectors'); %18 sectors at 4 km resolution
regions_4km=ncread(['/local/ModelData/ISMIP6Data/Processing/sectors_4km.nc'],'regions'); %3 regions (West, East and Peninsula)
numsectors=max(sectors_4km(:));
numregions=max(regions_4km(:));

%Find submissions and cleanup
submission_info = dir(folder_name);
for i=length(submission_info):-1:1,
	if length(submission_info(i).name)<3,
		 submission_info(i)=[];
	 end
end

for idir=18%1:length(submission_info),
	%Adjust ice and seawater density to the model
	if strcmp(submission_info(idir).name(1:4),'ILTS') | strcmp(submission_info(idir).name(1:3),'VUB') | strcmp(submission_info(idir).name(1:3),'VUW') | strcmp(submission_info(idir).name(1:3),'DOE') | strcmp(submission_info(idir).name(1:4),'IMAU'),
		ice_density = 910;
	elseif strcmp(submission_info(idir).name(1:4),'LSCE'),
		ice_density = 918;
	else
		ice_density = 917;
	end
	if strcmp(submission_info(idir).name(1:4),'UCSD') | strcmp(submission_info(idir).name(1:2),'DC') | strcmp(submission_info(idir).name(1:4),'LSCE') | strcmp(submission_info(idir).name(1:3),'DOE'),
		ocean_density = 1023;
	elseif strcmp(submission_info(idir).name(1:3),'PIK') | strcmp(submission_info(idir).name(1:3),'ULB'),
		ocean_density = 1027;
	elseif strcmp(submission_info(idir).name(1:4),'NCAR') | strcmp(submission_info(idir).name(1:5),'NORCE'),
		ocean_density = 1026;
	elseif strcmp(submission_info(idir).name(1:3),'UNN'),
		ocean_density = 1030;
	else
		ocean_density = 1028;
	end
	freshwater_density = 1000;
	
	%Clean up the experiments done to find actual simulations
	experiment_info=dir([folder_name '/' submission_info(idir).name]);
	for iexp=length(experiment_info):-1:1,
		if length(experiment_info(iexp).name)<3,
			experiment_info(iexp)=[];
		elseif strcmp(experiment_info(iexp).name(1:6),'compli') | strcmp(experiment_info(iexp).name(1:6),'README'),
			experiment_info(iexp)=[];
		end
	end

	%Find model resolution and get corresponding scaling map for area correction
	resolution=str2int(experiment_info(iexp).name(end-1:end));
	scalefac_model=scalefac(1:resolution:end,1:resolution:end);

	for iexp=4:length(experiment_info),
		file_info=dir([folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
		%Remove bad files
		for ifile=length(file_info):-1:1,
			if length(file_info(ifile).name)<3,
				file_info(ifile)=[];
			end
		end

		if step==1, % {{{Calculate ice volume
			found_lithk = 0;
			found_sftgif = 0;
			lim_vector=[];
			for isector=1:numsectors,
				eval(['lim_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['lim_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'lithk'),
					found_lithk = 1;
					lithk_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_lithk == 0 | found_sftgif ==0),
				error(['missing file lithk or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_lithk = double(ncread(lithk_file,'lithk'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_time = double(ncread(lithk_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;

			for itime=1:length(data_time),
				thickness_i=data_lithk(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				pos=find(mask_i==0); thickness_i(pos)=0;
				posnan=find(isnan(mask_i));
				thickness_i(posnan)=0; mask_i(posnan)=0;
				posnan=find(isnan(thickness_i));
				thickness_i(posnan)=0; mask_i(posnan)=0;
				vol=sum(thickness_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2;
				lim_total=vol*ice_density/(10^9*1000); %from m^3 to Gt
				lim_vector(itime)=lim_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					lim_total_sector=sum(thickness_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2*ice_density/(10^9*1000); %from m^3 to Gt
					eval(['lim_vector_sector' num2str(isector) '(itime)=lim_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					lim_total_region=sum(thickness_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2*ice_density/(10^9*1000); %from m^3 to Gt
					eval(['lim_vector_region' num2str(iregion) '(itime)=lim_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/ivol'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/ivol']);
			end
			explim_file=['ComputedScalars/' experimentname '/ivol/computed_ivol_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			explim_file
			status=WriteNetCDFComputedOutputs(explim_file,'ivol','ice volume','Gt',time_vector,lim_vector,...
				lim_vector_sector1,lim_vector_sector2,lim_vector_sector3,lim_vector_sector4,lim_vector_sector5,...
				lim_vector_sector6,lim_vector_sector7,lim_vector_sector8,lim_vector_sector9,lim_vector_sector10,...
				lim_vector_sector11,lim_vector_sector12,lim_vector_sector13,lim_vector_sector14,lim_vector_sector15,...
				lim_vector_sector16,lim_vector_sector17,lim_vector_sector18,...
				lim_vector_region1,lim_vector_region2,lim_vector_region3,...
				ice_density,ocean_density);
		end %end icevolume }}}
		if step==2, % {{{Calculate ice volume above floatation
			found_lithk = 0;
			found_topg= 0;
			found_sftgif = 0;
			found_sftgrf = 0;
			limnsw_vector=[];
			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'lithk'),
					found_lithk = 1;
					lithk_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:4),'topg'),
					found_topg= 1;
					topg_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_lithk == 0 | found_topg == 0 | found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file lithk, topg, sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_lithk = double(ncread(lithk_file,'lithk'));
			data_topg = double(ncread(topg_file,'topg'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(lithk_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;

			for itime=1:length(data_time),
				thickness_i=data_lithk(:,:,itime);
				bed_i=data_topg(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				groundmask_i=data_sftgrf(:,:,itime);
				pos=find(mask_i==0); thickness_i(pos)=0; 
				bed_i(pos)=0; groundmask_i(pos)=0;
				posnan=find(isnan(mask_i) | isnan(thickness_i) | isnan(bed_i) | isnan(groundmask_i));
				thickness_i(posnan)=0; mask_i(posnan)=0;
				bed_i(posnan)=0; groundmask_i(posnan)=0;
				hf_i=thickness_i+ocean_density/ice_density*min(bed_i,0);
				volaf=sum(hf_i(:).*mask_i(:).*groundmask_i(:).*scalefac_model(:))*(resolution*1000)^2;
				limnsw_total=volaf*ice_density/(10^9*1000); %from m^3 to Gt
				limnsw_vector(itime)=limnsw_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					limnsw_total_sector=sum((thickness_i(pos_sector) + ocean_density/ice_density*min(bed_i(pos_sector),0)).*mask_i(pos_sector).*groundmask_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2*ice_density/(10^9*1000); %from m^3 to Gt
					eval(['limnsw_vector_sector' num2str(isector) '(itime)=limnsw_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					limnsw_total_region=sum((thickness_i(pos_region) + ocean_density/ice_density*min(bed_i(pos_region),0)).*mask_i(pos_region).*groundmask_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2*ice_density/(10^9*1000); %from m^3 to Gt
					eval(['limnsw_vector_region' num2str(iregion) '(itime)=limnsw_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/ivaf'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/ivaf']);
			end
			explimnsw_file=['ComputedScalars/' experimentname '/ivaf/computed_ivaf_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			explimnsw_file
			status=WriteNetCDFComputedOutputs(explimnsw_file,'ivaf','ice volume above floatation','Gt',time_vector,limnsw_vector,...
				limnsw_vector_sector1,limnsw_vector_sector2,limnsw_vector_sector3,limnsw_vector_sector4,limnsw_vector_sector5,...
				limnsw_vector_sector6,limnsw_vector_sector7,limnsw_vector_sector8,limnsw_vector_sector9,limnsw_vector_sector10,...
				limnsw_vector_sector11,limnsw_vector_sector12,limnsw_vector_sector13,limnsw_vector_sector14,limnsw_vector_sector15,...
				limnsw_vector_sector16,limnsw_vector_sector17,limnsw_vector_sector18,...
				limnsw_vector_region1,limnsw_vector_region2,limnsw_vector_region3,...
				ice_density,ocean_density);
		end %end icevolume }}}
		if step==3, % {{{Calculate surface mass balance
			found_acabf = 0;
			found_sftgif = 0;
			tendacabf_vector=[];
			for isector=1:numsectors,
				eval(['tendacabf_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['tendacabf_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'acabf'),
					found_acabf = 1;
					acabf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_acabf == 0 | found_sftgif == 0 ),
				error(['missing file acabf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_acabf = double(ncread(acabf_file,'acabf'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_time = double(ncread(acabf_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			pos=find(data_sftgif<0); data_sftgif(pos)=0;

			for itime=1:length(data_time),
				acabf_i=data_acabf(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				posnan=find(isnan(mask_i) | isnan(acabf_i));
				acabf_i(posnan)=0; mask_i(posnan)=0;
				tendacabf_total=sum(acabf_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2; %in kg/s
				tendacabf_vector(itime)=tendacabf_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					tendacabf_total_sector=sum(acabf_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in kg/s
					eval(['tendacabf_vector_sector' num2str(isector) '(itime)=tendacabf_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					tendacabf_total_region=sum(acabf_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in kg/s
					eval(['tendacabf_vector_region' num2str(iregion) '(itime)=tendacabf_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/smb'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/smb']);
			end
			exptendacabf_file=['ComputedScalars/' experimentname '/smb/computed_smb_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			exptendacabf_file
			status=WriteNetCDFComputedOutputs(exptendacabf_file,'smb','spatially integrated surface mass balance','kg/s',time_vector,tendacabf_vector,...
				tendacabf_vector_sector1,tendacabf_vector_sector2,tendacabf_vector_sector3,tendacabf_vector_sector4,tendacabf_vector_sector5,...
				tendacabf_vector_sector6,tendacabf_vector_sector7,tendacabf_vector_sector8,tendacabf_vector_sector9,tendacabf_vector_sector10,...
				tendacabf_vector_sector11,tendacabf_vector_sector12,tendacabf_vector_sector13,tendacabf_vector_sector14,tendacabf_vector_sector15,...
				tendacabf_vector_sector16,tendacabf_vector_sector17,tendacabf_vector_sector18,...
				tendacabf_vector_region1,tendacabf_vector_region2,tendacabf_vector_region3,...
				ice_density,ocean_density);
		end %end surface mass balance }}}
		if step==4, % {{{Calculate basal melt under ice shelves
			found_libmassbffl = 0;
			found_sftgif = 0;
			found_sftflf = 0;
			tendlibmassbffl_vector=[];
			for isector=1:numsectors,
				eval(['tendlibmassbffl_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['tendlibmassbffl_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:11),'libmassbffl'),
					found_libmassbffl = 1;
					libmassbffl_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftflf'),
					found_sftflf= 1;
					sftflf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_libmassbffl == 0 | found_sftgif == 0 | found_sftflf == 0),
				error(['missing file libmassbffl, sftflf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_libmassbffl = double(ncread(libmassbffl_file,'libmassbffl'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftflf = double(ncread(sftflf_file,'sftflf'));
			data_time = double(ncread(libmassbffl_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftflf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftflf(:))>1 | min(data_sftflf(:))<0), 
				disp(['sftflf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftflf>1); data_sftflf(pos)=1;

			for itime=1:length(data_time),
				libmassbffl_i=data_libmassbffl(:,:,itime);
				shelfmask_i=data_sftflf(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				pos=find(mask_i==0); 
				libmassbffl_i(pos)=0; shelfmask_i(pos)=0;
				posnan=find(isnan(mask_i) | isnan(libmassbffl_i) | isnan(shelfmask_i));
				libmassbffl_i(posnan)=0; mask_i(posnan)=0; shelfmask_i(posnan)=0;
				tendlibmassbffl_total=sum(libmassbffl_i(:).*shelfmask_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2; %in kg/s
				tendlibmassbffl_vector(itime)=tendlibmassbffl_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					tendlibmassbffl_total_sector=sum(libmassbffl_i(pos_sector).*shelfmask_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in kg/s
					eval(['tendlibmassbffl_vector_sector' num2str(isector) '(itime)=tendlibmassbffl_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					tendlibmassbffl_total_region=sum(libmassbffl_i(pos_region).*shelfmask_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in kg/s
					eval(['tendlibmassbffl_vector_region' num2str(iregion) '(itime)=tendlibmassbffl_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/shelfmelt'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/shelfmelt']);
			end
			exptendlibmassbffl_file=['ComputedScalars/' experimentname '/shelfmelt/computed_shelfmelt_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			exptendlibmassbffl_file
			status=WriteNetCDFComputedOutputs(exptendlibmassbffl_file,'shelfmelt','spatially integrated ice shelf basal melt','kg/s',time_vector,tendlibmassbffl_vector,...
				tendlibmassbffl_vector_sector1,tendlibmassbffl_vector_sector2,tendlibmassbffl_vector_sector3,tendlibmassbffl_vector_sector4,tendlibmassbffl_vector_sector5,...
				tendlibmassbffl_vector_sector6,tendlibmassbffl_vector_sector7,tendlibmassbffl_vector_sector8,tendlibmassbffl_vector_sector9,tendlibmassbffl_vector_sector10,...
				tendlibmassbffl_vector_sector11,tendlibmassbffl_vector_sector12,tendlibmassbffl_vector_sector13,tendlibmassbffl_vector_sector14,tendlibmassbffl_vector_sector15,...
				tendlibmassbffl_vector_sector16,tendlibmassbffl_vector_sector17,tendlibmassbffl_vector_sector18,...
				tendlibmassbffl_vector_region1,tendlibmassbffl_vector_region2,tendlibmassbffl_vector_region3,...
				ice_density,ocean_density);
		end %end ice shelf basal melt }}}
		if step==5, % {{{Calculate floating area
			found_sftgif = 0;
			found_sftflf = 0;
			iareafl_vector = [];
			for isector=1:numsectors,
				eval(['iareafl_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['iareafl_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:6),'sftflf'),
					found_sftflf= 1;
					sftflf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_sftgif == 0 | found_sftflf == 0),
				error(['missing file sftflf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftflf = double(ncread(sftflf_file,'sftflf'));
			data_time = double(ncread(sftflf_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftflf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftflf(:))>1 | min(data_sftflf(:))<0), 
				disp(['sftflf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftflf>1); data_sftflf(pos)=1;

			for itime=1:length(data_time),
				shelfmask_i=data_sftflf(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				pos=find(mask_i==0); 
				shelfmask_i(pos)=0;
				posnan=find(isnan(mask_i) | isnan(shelfmask_i));
				mask_i(posnan)=0; shelfmask_i(posnan)=0;
				iareafl_total=sum(shelfmask_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2; %in m^2
				iareafl_vector(itime)=iareafl_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					iareafl_total_sector=sum(shelfmask_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in m^2
					eval(['iareafl_vector_sector' num2str(isector) '(itime)=iareafl_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					iareafl_total_region=sum(shelfmask_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in m^2
					eval(['iareafl_vector_region' num2str(iregion) '(itime)=iareafl_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/iareafl'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/iareafl']);
			end
			expiareafl_file=['ComputedScalars/' experimentname '/iareafl/computed_iareafl_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			expiareafl_file
			status=WriteNetCDFComputedOutputs(expiareafl_file,'iareafl','floating ice area','m^2',time_vector,iareafl_vector,...
				iareafl_vector_sector1,iareafl_vector_sector2,iareafl_vector_sector3,iareafl_vector_sector4,iareafl_vector_sector5,...
				iareafl_vector_sector6,iareafl_vector_sector7,iareafl_vector_sector8,iareafl_vector_sector9,iareafl_vector_sector10,...
				iareafl_vector_sector11,iareafl_vector_sector12,iareafl_vector_sector13,iareafl_vector_sector14,iareafl_vector_sector15,...
				iareafl_vector_sector16,iareafl_vector_sector17,iareafl_vector_sector18,...
				iareafl_vector_region1,iareafl_vector_region2,iareafl_vector_region3,...
				ice_density,ocean_density);
		end %end ice shelf area }}}

		if step==6, % {{{Calculate grounded area
			found_sftgif = 0;
			found_sftgrf = 0;
			iareagr_vector = [];
			for isector=1:numsectors,
				eval(['iareagr_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['iareagr_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(sftgrf_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;

			for itime=1:length(data_time),
				shelfmask_i=data_sftgrf(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				pos=find(mask_i==0); 
				shelfmask_i(pos)=0;
				posnan=find(isnan(mask_i) | isnan(shelfmask_i));
				mask_i(posnan)=0; shelfmask_i(posnan)=0;
				iareagr_total=sum(shelfmask_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2; %in m^2
				iareagr_vector(itime)=iareagr_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					iareagr_total_sector=sum(shelfmask_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in m^2
					eval(['iareagr_vector_sector' num2str(isector) '(itime)=iareagr_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					iareagr_total_region=sum(shelfmask_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in m^2
					eval(['iareagr_vector_region' num2str(iregion) '(itime)=iareagr_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/iareagr'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/iareagr']);
			end
			expiareagr_file=['ComputedScalars/' experimentname '/iareagr/computed_iareagr_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			expiareagr_file
			status=WriteNetCDFComputedOutputs(expiareagr_file,'iareagr','grounded ice area','m^2',time_vector,iareagr_vector,...
				iareagr_vector_sector1,iareagr_vector_sector2,iareagr_vector_sector3,iareagr_vector_sector4,iareagr_vector_sector5,...
				iareagr_vector_sector6,iareagr_vector_sector7,iareagr_vector_sector8,iareagr_vector_sector9,iareagr_vector_sector10,...
				iareagr_vector_sector11,iareagr_vector_sector12,iareagr_vector_sector13,iareagr_vector_sector14,iareagr_vector_sector15,...
				iareagr_vector_sector16,iareagr_vector_sector17,iareagr_vector_sector18,...
				iareagr_vector_region1,iareagr_vector_region2,iareagr_vector_region3,...
				ice_density,ocean_density);
		end %end grounded ice area }}}
		if step==7, % {{{Calculate total ice area
			found_sftgif = 0;
			icearea_vector = [];
			for isector=1:numsectors,
				eval(['icearea_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['icearea_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_sftgif == 0),
				error(['missing file sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_time = double(ncread(sftgif_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;

			for itime=1:length(data_time),
				mask_i=data_sftgif(:,:,itime);
				posnan=find(isnan(mask_i));
				mask_i(posnan)=0;
				icearea_total=sum(mask_i(:).*scalefac_model(:))*(resolution*1000)^2; %in m^2
				icearea_vector(itime)=icearea_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					icearea_total_sector=sum(mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in m^2
					eval(['icearea_vector_sector' num2str(isector) '(itime)=icearea_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					icearea_total_region=sum(mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in m^2
					eval(['icearea_vector_region' num2str(iregion) '(itime)=icearea_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/icearea'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/icearea']);
			end
			expicearea_file=['ComputedScalars/' experimentname '/icearea/computed_icearea_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			expicearea_file
			status=WriteNetCDFComputedOutputs(expicearea_file,'icearea','total ice area','m^2',time_vector,icearea_vector,...
				icearea_vector_sector1,icearea_vector_sector2,icearea_vector_sector3,icearea_vector_sector4,icearea_vector_sector5,...
				icearea_vector_sector6,icearea_vector_sector7,icearea_vector_sector8,icearea_vector_sector9,icearea_vector_sector10,...
				icearea_vector_sector11,icearea_vector_sector12,icearea_vector_sector13,icearea_vector_sector14,icearea_vector_sector15,...
				icearea_vector_sector16,icearea_vector_sector17,icearea_vector_sector18,...
				icearea_vector_region1,icearea_vector_region2,icearea_vector_region3,...
				ice_density,ocean_density);
		end %end total ice area }}}
		if step==8, % {{{Calculate surface mass balance on grounded ice
			found_acabf = 0;
			found_sftgif = 0;
			found_sftgrf = 0;
			tendacabfgr_vector=[];
			for isector=1:numsectors,
				eval(['tendacabfgr_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['tendacabfgr_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'acabf'),
					found_acabf = 1;
					acabf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_acabf == 0 | found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file acabf, sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_acabf = double(ncread(acabf_file,'acabf'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(acabf_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;

			for itime=1:length(data_time),
				acabf_i=data_acabf(:,:,itime);
				mbfgr_totalask_i=data_sftgif(:,:,itime);
				maskgr_i=data_sftgrf(:,:,itime);
				pos=find(maskgr_i==0); acabf_i(pos)=0; 
				bed_i(pos)=0; maskgr_i(pos)=0;
				pos=find(maskgr_i==0); acabf_i(pos)=0; 
				posnan=find(isnan(maskgr_i) | isnan(acabf_i));
				acabf_i(posnan)=0; maskgr_i(posnan)=0;
				tendacabfgr_total=sum(acabf_i(:).*maskgr_i(:).*scalefac_model(:))*(resolution*1000)^2; %in kg/s
				tendacabfgr_vector(itime)=tendacabfgr_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					tendacabfgr_total_sector=sum(acabf_i(pos_sector).*maskgr_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2; %in kg/s
					eval(['tendacabfgr_vector_sector' num2str(isector) '(itime)=tendacabfgr_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					tendacabfgr_total_region=sum(acabf_i(pos_region).*maskgr_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2; %in kg/s
					eval(['tendacabfgr_vector_region' num2str(iregion) '(itime)=tendacabfgr_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/smbgr'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/smbgr']);
			end
			exptendacabfgr_file=['ComputedScalars/' experimentname '/smbgr/computed_smbgr_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			exptendacabfgr_file
			status=WriteNetCDFComputedOutputs(exptendacabfgr_file,'smbgr','spatially integrated surface mass balance over grounded ice','kg/s',time_vector,tendacabfgr_vector,...
				tendacabfgr_vector_sector1,tendacabfgr_vector_sector2,tendacabfgr_vector_sector3,tendacabfgr_vector_sector4,tendacabfgr_vector_sector5,...
				tendacabfgr_vector_sector6,tendacabfgr_vector_sector7,tendacabfgr_vector_sector8,tendacabfgr_vector_sector9,tendacabfgr_vector_sector10,...
				tendacabfgr_vector_sector11,tendacabfgr_vector_sector12,tendacabfgr_vector_sector13,tendacabfgr_vector_sector14,tendacabfgr_vector_sector15,...
				tendacabfgr_vector_sector16,tendacabfgr_vector_sector17,tendacabfgr_vector_sector18,...
				tendacabfgr_vector_region1,tendacabfgr_vector_region2,tendacabfgr_vector_region3,...
				ice_density,ocean_density);
		end %end surface mass balance }}}
		if step==9, % {{{Calculate sea level directly with no correction
			found_lithk = 0;
			found_topg= 0;
			found_sftgif = 0;
			found_sftgrf = 0;
			limnsw_vector=[];
			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'lithk'),
					found_lithk = 1;
					lithk_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:4),'topg'),
					found_topg= 1;
					topg_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_lithk == 0 | found_topg == 0 | found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file lithk, topg, sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_lithk = double(ncread(lithk_file,'lithk'));
			data_topg = double(ncread(topg_file,'topg'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(lithk_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;

			for itime=1:length(data_time),
				thickness_i=data_lithk(:,:,itime);
				bed_i=data_topg(:,:,itime);
				mask_i=data_sftgif(:,:,itime);
				groundmask_i=data_sftgrf(:,:,itime);
				pos=find(mask_i==0); thickness_i(pos)=0; 
				bed_i(pos)=0; groundmask_i(pos)=0;
				posnan=find(isnan(mask_i) | isnan(thickness_i) | isnan(bed_i) | isnan(groundmask_i));
				thickness_i(posnan)=0; mask_i(posnan)=0;
				bed_i(posnan)=0; groundmask_i(posnan)=0;
				hf_i=thickness_i+ocean_density/ice_density*min(bed_i,0);
				volaf=sum(hf_i(:).*mask_i(:).*groundmask_i(:).*scalefac_model(:))*(resolution*1000)^2;
				limnsw_total=-volaf*ice_density/(362.5*10^12*ocean_density); %m SLE
				limnsw_vector(itime)=limnsw_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					limnsw_total_sector=-sum((thickness_i(pos_sector) + ocean_density/ice_density*min(bed_i(pos_sector),0).*groundmask_i(pos_sector)).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2*ice_density/(362.5*10^12*ocean_density); %m SLE
					eval(['limnsw_vector_sector' num2str(isector) '(itime)=limnsw_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					limnsw_total_region=-sum((thickness_i(pos_region) + ocean_density/ice_density*min(bed_i(pos_region),0).*groundmask_i(pos_region)).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2*ice_density/(362.5*10^12*ocean_density); %m SLE
					eval(['limnsw_vector_region' num2str(iregion) '(itime)=limnsw_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/sle'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/sle']);
			end
			explimnsw_file=['ComputedScalars/' experimentname '/sle/computed_sle_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			explimnsw_file
			status=WriteNetCDFComputedOutputs(explimnsw_file,'sle','sea level equivalent','m',time_vector,limnsw_vector,...
				limnsw_vector_sector1,limnsw_vector_sector2,limnsw_vector_sector3,limnsw_vector_sector4,limnsw_vector_sector5,...
				limnsw_vector_sector6,limnsw_vector_sector7,limnsw_vector_sector8,limnsw_vector_sector9,limnsw_vector_sector10,...
				limnsw_vector_sector11,limnsw_vector_sector12,limnsw_vector_sector13,limnsw_vector_sector14,limnsw_vector_sector15,...
				limnsw_vector_sector16,limnsw_vector_sector17,limnsw_vector_sector18,...
				limnsw_vector_region1,limnsw_vector_region2,limnsw_vector_region3,...
				ice_density,ocean_density);
		end %end icevolume }}}
		if step==10, % {{{Calculate sea level with correction from Goelzer 2020 
			found_lithk = 0;
			found_topg= 0;
			found_sftgif = 0;
			found_sftgrf = 0;
			limnsw_vector=[];

			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'lithk'),
					found_lithk = 1;
					lithk_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:4),'topg'),
					found_topg= 1;
					topg_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_lithk == 0 | found_topg == 0 | found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file lithk, topg, sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_lithk = double(ncread(lithk_file,'lithk'));
			data_topg = double(ncread(topg_file,'topg'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(lithk_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;
			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=zeros(length(data_time),1);'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=zeros(length(data_time),1);']);
			end
			limnsw_vector=zeros(length(data_time),1);

			for itime=1:length(data_time),
				thickness_i=data_lithk(:,:,itime);
				if count(topg_file,'UNN_Ua') %use initial bed in UNN because bed constant and masked out when ice retreats
					bed_i=data_topg(:,:,1);
				else
					bed_i=data_topg(:,:,itime);
				end
				mask_i=data_sftgif(:,:,itime);
				groundmask_i=data_sftgrf(:,:,itime);
				pos=find(mask_i==0); thickness_i(pos)=0; groundmask_i(pos)=0;
				posnan=find(isnan(mask_i)); mask_i(posnan)=0;
				posnan=find(isnan(groundmask_i)); groundmask_i(posnan)=0;
				posnan=find(isnan(thickness_i)); thickness_i(posnan)=0;
				posnan=find(isnan(bed_i)); bed_i(posnan)=0;
				hf_i=thickness_i+ocean_density/ice_density*min(bed_i,0);
				ho_i=max(-bed_i,0);
				hden_i=thickness_i*ice_density*(1/freshwater_density - 1/ocean_density);
				volaf=sum(hf_i(:).*mask_i(:).*groundmask_i(:).*scalefac_model(:))*(resolution*1000)^2;
				voloc=sum(ho_i(:).*scalefac_model(:))*(resolution*1000)^2;
				volden=sum(hden_i(:).*mask_i(:).*scalefac_model(:))*(resolution*1000)^2;
				limnsw_total=-1*volaf*ice_density/(362.5*10^12*ocean_density)-1*voloc/(362.5*10^12)-1*volden/(362.5*10^12); %in m SLE
				limnsw_vector(itime)=limnsw_total;
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					volaf=sum(hf_i(pos_sector).*mask_i(pos_sector).*groundmask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2;
					voloc=sum(ho_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2;
					volden=sum(hden_i(pos_sector).*mask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2;
					limnsw_total_sector=-1*volaf*ice_density/(362.5*10^12*ocean_density)-1*voloc/(362.5*10^12)-1*volden/(362.5*10^12); %in m SLE
					eval(['limnsw_vector_sector' num2str(isector) '(itime)=limnsw_total_sector;'])
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					volaf=sum(hf_i(pos_region).*mask_i(pos_region).*groundmask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2;
					voloc=sum(ho_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2;
					volden=sum(hden_i(pos_region).*mask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2;
					limnsw_total_region=-1*volaf*ice_density/(362.5*10^12*ocean_density)-1*voloc/(362.5*10^12)-1*volden/(362.5*10^12); %in m SLE
					eval(['limnsw_vector_region' num2str(iregion) '(itime)=limnsw_total_region;'])
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/sle_goelzer'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/sle_goelzer']);
			end
			explimnsw_file=['ComputedScalars/' experimentname '/sle_goelzer/computed_sle_goelzer_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			explimnsw_file
			status=WriteNetCDFComputedOutputs(explimnsw_file,'sle_goelzer','sea level equivalent with Goelzer correction','m',...
				time_vector,limnsw_vector,...
				limnsw_vector_sector1,limnsw_vector_sector2,limnsw_vector_sector3,limnsw_vector_sector4,limnsw_vector_sector5,...
				limnsw_vector_sector6,limnsw_vector_sector7,limnsw_vector_sector8,limnsw_vector_sector9,limnsw_vector_sector10,...
				limnsw_vector_sector11,limnsw_vector_sector12,limnsw_vector_sector13,limnsw_vector_sector14,limnsw_vector_sector15,...
				limnsw_vector_sector16,limnsw_vector_sector17,limnsw_vector_sector18,...
				limnsw_vector_region1,limnsw_vector_region2,limnsw_vector_region3,...
				ice_density,ocean_density);
		end %end icevolume }}}

		if step==11, % {{{Calculate sea level with correction from Adhikari 2020 
			found_lithk = 0;
			found_topg= 0;
			found_sftgif = 0;
			found_sftgrf = 0;
			limnsw_vector=[];

			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=[];'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=[];'])
			end
			for ifile=1:length(file_info),
				if strcmp(file_info(ifile).name(1:5),'lithk'),
					found_lithk = 1;
					lithk_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:4),'topg'),
					found_topg= 1;
					topg_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgif'),
					found_sftgif= 1;
					sftgif_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				elseif strcmp(file_info(ifile).name(1:6),'sftgrf'),
					found_sftgrf= 1;
					sftgrf_file=[folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name '/' file_info(ifile).name];
				end
			end
			if (found_lithk == 0 | found_topg == 0 | found_sftgif == 0 | found_sftgrf == 0),
				error(['missing file lithk, topg, sftgrf or sftgif in ' folder_name '/' submission_info(idir).name '/' experiment_info(iexp).name]);
			end

			data_lithk = double(ncread(lithk_file,'lithk'));
			data_topg = double(ncread(topg_file,'topg'));
			data_sftgif = double(ncread(sftgif_file,'sftgif'));
			data_sftgrf = double(ncread(sftgrf_file,'sftgrf'));
			data_time = double(ncread(lithk_file,'time'));
			time_vector=2015:2015+length(data_time)-1;
			%sftgif and sftgrf should be between 0 and 1
			if(max(data_sftgif(:))>1 | min(data_sftgif(:))<0), 
				disp(['sftgif should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgif>1); data_sftgif(pos)=1;
			if(max(data_sftgrf(:))>1 | min(data_sftgrf(:))<0), 
				disp(['sftgrf should be between 0 and 1 in model ' submission_info(idir).name '/' experiment_info(iexp).name]); 
			end
			pos=find(data_sftgrf>1); data_sftgrf(pos)=1;
			for isector=1:numsectors,
				eval(['limnsw_vector_sector' num2str(isector) '=zeros(length(data_time),1);'])
			end
			for iregion=1:numregions,
				eval(['limnsw_vector_region' num2str(iregion) '=zeros(length(data_time),1);']);
			end
			limnsw_vector=zeros(length(data_time),1);

			for itime=1:length(data_time),
				thickness_i=data_lithk(:,:,itime);
				if count(topg_file,'UNN_Ua') %use initial bed in UNN because bed constant and masked out when ice retreats
					bed_i=data_topg(:,:,1);
				else
					bed_i=data_topg(:,:,itime);
				end
				mask_i=data_sftgif(:,:,itime);
				groundmask_i=data_sftgrf(:,:,itime);
				pos=find(mask_i==0); thickness_i(pos)=0; groundmask_i(pos)=0;
				posnan=find(isnan(mask_i)); mask_i(posnan)=0; thickness_i(posnan)=0; groundmask_i(posnan)=0;
				posnan=find(isnan(groundmask_i)); groundmask_i(posnan)=0;
				posnan=find(isnan(thickness_i)); thickness_i(posnan)=0;
				posnan=find(isnan(bed_i)); bed_i(posnan)=0;
				if itime==1,
					hf_i=thickness_i+ocean_density/ice_density*min(bed_i,0);
					volaf=sum(hf_i(:).*mask_i(:).*groundmask_i(:).*scalefac_model(:))*(resolution*1000)^2;
					limnsw_total=-volaf*ice_density/(362.5*10^12*ocean_density);
					limnsw_vector(itime)=limnsw_total;
				else
					thickness_im=data_lithk(:,:,itime-1); 
					if count(topg_file,'UNN_Ua') %use initial bed in UNN because bed constant and masked out when ice retreats
						bed_im=data_topg(:,:,1);
					else
						bed_im=data_topg(:,:,itime-1); 
					end
					mask_im=data_sftgif(:,:,itime-1); 
					groundmask_im=data_sftgrf(:,:,itime-1); 
					pos=find(mask_im==0); thickness_im(pos)=0; groundmask_im(pos)=0;
					posnan=find(isnan(mask_im)); mask_im(posnan)=0; thickness_im(posnan)=0; groundmask_im(posnan)=0;
					posnan=find(isnan(groundmask_im)); groundmask_im(posnan)=0;
					posnan=find(isnan(thickness_im)); thickness_im(posnan)=0;
					posnan=find(isnan(bed_im)); bed_im(posnan)=0;

					dh_i=thickness_i-thickness_im;
					dhf_i=(thickness_i+ocean_density/ice_density*min(bed_i,0)).*groundmask_i... 
						-(thickness_im+ocean_density/ice_density*min(bed_im,0)).*groundmask_im; %assuming sea level constant at 0
					dhs_i=(dh_i-freshwater_density/ocean_density*(dh_i-dhf_i).*(1-groundmask_im.*groundmask_i)).*mask_im.*mask_i;
					volaf=sum(dhs_i(:).*scalefac_model(:))*(resolution*1000)^2;
					limnsw_total=-volaf*ice_density/(362.5*10^12*freshwater_density);

					limnsw_vector(itime)=limnsw_vector(itime-1)+limnsw_total;
				end
				for isector=1:numsectors,
					eval(['sectors=sectors_' num2str(resolution) 'km;'])
					pos_sector=find(sectors==isector);
					if itime==1
						volaf=sum(hf_i(pos_sector).*mask_i(pos_sector).*groundmask_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2;
						limnsw_total_sector=-volaf*ice_density/(362.5*10^12*ocean_density);
						eval(['limnsw_vector_sector' num2str(isector) '(itime)=limnsw_total_sector;'])
					else
						volaf=sum(dhs_i(pos_sector).*scalefac_model(pos_sector))*(resolution*1000)^2;
						limnsw_total_sector=-volaf*ice_density/(362.5*10^12*ocean_density);
						eval(['limnsw_vector_sector' num2str(isector) '(itime)=limnsw_vector_sector' num2str(isector) '(itime-1)+limnsw_total_sector;'])
					end
				end
				for iregion=1:numregions,
					eval(['regions=regions_' num2str(resolution) 'km;'])
					pos_region=find(regions==iregion);
					if itime==1
						volaf=sum(hf_i(pos_region).*mask_i(pos_region).*groundmask_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2;
						limnsw_total_region=-volaf*ice_density/(362.5*10^12*ocean_density);
						eval(['limnsw_vector_region' num2str(iregion) '(itime)=limnsw_total_region;'])
					else
						volaf=sum(dhs_i(pos_region).*scalefac_model(pos_region))*(resolution*1000)^2;
						limnsw_total_region=-volaf*ice_density/(362.5*10^12*ocean_density);
						eval(['limnsw_vector_region' num2str(iregion) '(itime)=limnsw_vector_region' num2str(iregion) '(itime-1)+limnsw_total_region;'])
					end
				end
			end %end of time

			%Write results in netcdf file
			experimentname = extractBefore(experiment_info(iexp).name,'_')
			if exist(['ComputedScalars/' experimentname '/sle_adhikari'],'dir')==0,
				eval(['mkdir ComputedScalars/' experimentname '/sle_adhikari']);
			end
			explimnsw_file=['ComputedScalars/' experimentname '/sle_adhikari/computed_sle_adhikari_AIS_' submission_info(idir).name '_' experimentname '.nc'];
			explimnsw_file
			status=WriteNetCDFComputedOutputs(explimnsw_file,'sle_adhikari','sea level equivalent with Goelzer correction','m',...
				time_vector,limnsw_vector,...
				limnsw_vector_sector1,limnsw_vector_sector2,limnsw_vector_sector3,limnsw_vector_sector4,limnsw_vector_sector5,...
				limnsw_vector_sector6,limnsw_vector_sector7,limnsw_vector_sector8,limnsw_vector_sector9,limnsw_vector_sector10,...
				limnsw_vector_sector11,limnsw_vector_sector12,limnsw_vector_sector13,limnsw_vector_sector14,limnsw_vector_sector15,...
				limnsw_vector_sector16,limnsw_vector_sector17,limnsw_vector_sector18,...
				limnsw_vector_region1,limnsw_vector_region2,limnsw_vector_region3,...
				ice_density,ocean_density);
		end %end icevolume }}}

	end
end

