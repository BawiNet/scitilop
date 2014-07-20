var firstTheme = 'lNWPc_ds';
var c_green = 120;
var c_red = 10;
var c_blue = 210;
var c_purple = 250;
var crgb_null = "#E0E0E0";
var crgb_default = "#000000";
var base_saturation = 35;
var base_lightness = 10;

var sgg_layer;
var themes = document.getElementById('menu-ui');
var map = L.map('map').setView([35.9665, 127.9], 7.5);
var firstFlag = true;


if (getUrlVars()["tc"]!=null) {
	firstTheme =getUrlVars()["tc"]; 
};

var themeCode = firstTheme;

//addLayer(L.mapbox.tileLayer('yonghah.iecpg49d'), 'Base Map', 1);

sgg_len = sgg.features.length;
//alert( sgg_len );

sgg_layer = L.geoJson([sgg], {
	style: 	sgg_style,
	onEachFeature: onEachFeature,
	});
sgg_layer.addTo(map);

map.attributionControl.addAttribution('');

var info = L.control();

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update(themeCode);
    return this._div;
};

// method that we will use to update the control based on feature properties passed
info.update = function (tc) {
    this._div.innerHTML = '<a href="./index.html"><h4>2014년 지방선거</h4></a>' + '<br>'
    	+ '<a href="http://www.ilwar.com/poli/141022" target="_blank">지도들에 대한 해제</a>' + '<br><br>'
    	+ "<b>"+getThemeName(tc) + '</b><br>'
    	+ getThemeDesc(tc) ;
};

info.addTo(map);

function addThemeButton(themeText) {
	var tc = themeText;
	var link = document.createElement('a');
        link.href = '#';
        link.className = 'active';
        link.innerHTML = getThemeName(tc);
        
    link.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        themeCode = tc;
        sgg_layer.setStyle(sgg_style);
        info.update(tc);
        console.log(tc);
        //window.location.href = "./index.html?tc="+tc;
	};
    themes.appendChild(link);
}

function addLayer(layer, name, zIndex) {
    layer.setZIndex(zIndex).addTo(map);
    map.addLayer(layer);
    this.className = 'active';
}

function get_color( sig_cd, sig_nm ) {
	vote_percent = election_data['2012-04-11'][sig_cd]['elect_data']['vote_percent'] / 100;
	party_nm = election_data['2012-04-11'][sig_cd]['elect_data']['party_nm'];
	//alert( vote_percent + ":" + sig_cd + party_nm );
	//ccode = setBipoleColor(d,-1,1,red2Blue);
	
	if( party_nm == '새누리당' ) {
		//vote_percent *= 1;		
		color = setBipoleColor( vote_percent , -1, 1, 1 );
		
	} else if( party_nm == '민주통합당' ){
		//vote_percent *= -1;	
		color = setBipoleColor( vote_percent * -1, -1, 1, 1 );
	} else {
		//alert( sig_cd, sig_nm, "white!" );
		color = "#BBBBBB";
	}
	//alert( color );
	return color;	
	
}
function sgg_style (feature) {
	var cValue = feature.properties[themeCode];
	var fillColorValue = '#FFFFFF';
	if( typeof feature.properties['sig_cd'] !== "undefined") {
		sig_cd = feature.properties['sig_cd'] 
		sig_nm = feature.properties['sig_nm'] 
		fillColorValue = get_color( sig_cd, sig_nm );
	}
	//alert( feature.properties['sig_cd'] );
	//alert( feature.properties['TL_SCCO_1'] );
	return {
		fillColor: fillColorValue,
        weight: .8,
        opacity: 1,
        color: '#303030',
        dashArray: '1',
        fillOpacity: 1
	};	
}

function onEachFeature(feature, layer) {
	var tc_list = Object.keys(feature.properties);
	var tc_length = tc_list.length;
	if (firstFlag) {
		for (var i = 0; i < tc_length; i++) {
			var tct = tc_list[i];
			if (needButton(tct)) addThemeButton(tct); 
		}
		firstFlag = false;
	}
	var ppText = "<b>"+feature.properties.TL_SCCO_1 + "</b>"+"<br>"
	
	for (var i = 0; i < tc_length; i++) {
		var tct = tc_list[i];
		if (needButton(tct)){
			var cText = " " +getThemeName(tct) + " =" + feature.properties[tct]+"<br>";
			ppText += cText;
		}
	}

	layer.bindPopup(ppText,{minWidth:250,
							maxWidth:400, 
							maxHeight:150, 
							autoPan: true, 
							closeButton: true});
}

function needButton(tct) {
	var needButton = false;
	if ((["gid","sig_cd","sig_eng_nm","area","TL_SCCO_SI","TL_SCCO_1","dis_NLp","NPPc_ds","lNPPc_ds"].indexOf(tct)<0) 
		&& (tct.indexOf("prop") ==-1)
		&& (tct.indexOf("prov") ==-1)
		&& (tct.indexOf("2012p") ==-1)
		&& tct == "S1st") {
			needButton = true;
		}
	return needButton;
}

function setColor(d,tc) {
	var ccode = crgb_default;
	var min = Math.min(minDummy[themeCode],maxDummy[themeCode]);
	var max = Math.max(minDummy[themeCode],maxDummy[themeCode]);
	
	var red2Blue = 1;
	var blue2Red = -1;
	
	if (["S1st","S1st_2nd","dis","2012p_2012","2012p_20_1"].indexOf(tc)>=0) {
		ccode = setMonoColor(d,min,max,c_green);
	}
	if (["NWP_1st","NWP_12","NWP_party","NWP_ptcd_r","2012_NWP","NWPc_p"].indexOf(tc)>=0) {
		ccode = setMonoColor(d,min,max,c_red);
	}
	if (["NPP_1st","NPP_12","NPP_party","NPP_ptcd_r","2012_NPP","NPPc_p"].indexOf(tc)>=0) {
		ccode = setMonoColor(d,min,max,c_blue);
	}
	if (["noparty_1s","noparty_12","NL_party","PD_party"].indexOf(tc)>=0) {
		ccode = setMonoColor(d,min,max,c_purple);
	}
	if (["NWP_cdpt","lNWPOPP","NPPOPP","NPP_cdpt2","dis_NLp","NWP_2012d","NWPc_ds","lNWPc_ds"].indexOf(tc)>=0) {
		ccode = setBipoleColor(d,min,max,red2Blue);
	}
	if (["NPP_cdpt","NPP_2012d","OPP_2012d","NPPc_ds","lNPPc_ds"].indexOf(tc)>=0) {
		ccode = setBipoleColor(d,min,max,blue2Red);
	}
	return ccode;
}

function setMonoColor(d,min,max,hue) {
	var ccode;
	if (d == null) ccode = crgb_null;
	else {
		var scaled = d /(max-min);
		var lightness = (1-scaled) *(100-base_lightness);
		var hsl = new HSLColour(hue,base_saturation,base_lightness+lightness);
		ccode = hsl.getCSSHexadecimalRGB();
	}
	return ccode;
}

function setBipoleColor(d,min,max,direction) {
	var ccode;
	var scaled;
	d = d * direction;
	
	// direction = 1 means high in red direction-1 means high in blue
	if (d == null) ccode = crgb_null;
	else if (d>0) {
		scaled = d / max;
		lightness= (1 - scaled)*(100-base_lightness);
		hsl = new HSLColour(c_red,base_saturation,base_lightness+lightness);
		ccode = hsl.getCSSHexadecimalRGB();
	}
	
	else if (d<0) {
		scaled = d / Math.abs(min);
		lightness= (1 + scaled)*(100-base_lightness);
		hsl = new HSLColour(c_blue,base_saturation,base_lightness+lightness);
		ccode = hsl.getCSSHexadecimalRGB();
	}
	else ccode = '#FFFFFF';
	
	return ccode;
}

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

function getThemeName (tc) {
	var themeDict = {};
	themeDict["S1st"] = "[기초] 당선자 득표율";
	
	var tName = themeDict[tc];
	if (tName == null) tName = tc;
	return tName;
}

function getThemeDesc (tc) {
	var desc = "";
	var descDict = {
		"S1st":"기초자치단체장 선거 당선자의 득표율",
	};  
	desc = descDict[tc];
	if (desc == null) desc = "";
	return desc;
}
