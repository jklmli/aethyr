import flash.filters.BitmapFilterQuality;
import flash.filters.GlowFilter;
import fl.transitions.Tween;
import fl.transitions.TweenEvent;
import fl.transitions.easing.*;

var aux1;

download.mouseChildren = false;
download.buttonMode = true;
download.useHandCursor = true;

download.addEventListener("mouseOver", mouseOverHandler);
download.addEventListener("mouseOut", mouseOutHandler);

var downloadGlow:GlowFilter = new GlowFilter(0xD13083, 1, 2, 2, 2, 3, false, false);

var downloadGlowX:Tween = new Tween(downloadGlow, "blurX", Regular.easeOut, 2, 2, 1, true);
var downloadGlowY:Tween = new Tween(downloadGlow, "blurY", Regular.easeOut, 2, 2, 1, true);

downloadGlowX.addEventListener("motionChange", downloadFunc);

function downloadFunc(e:TweenEvent) {
	download.filters = [downloadGlow];
}

function mouseOverHandler(e:MouseEvent):void {
	aux1 = e.target.name;
	downloadGlowX.continueTo(10, 0.5);
	downloadGlowY.continueTo(10, 0.5);
}
function mouseOutHandler(e:MouseEvent):void {
	downloadGlowX.continueTo(2, 1);
	downloadGlowY.continueTo(2, 1);
}