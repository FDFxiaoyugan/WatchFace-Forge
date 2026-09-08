# WFF v5 Element/Attribute Inventory

Source: `google/watchface` → `third_party/wff/specification/documents/5`

XSD files: 99 | Elements: 90 | Enums: 29

---

## BitmapFonts (4)

### `<BitmapFont>`

- **Children:** `<Character>`, `<Word>`
- **Attributes:**
  - `@name` (xs:string) **(required)**
- *Defined in: `bitmapFontsElement.xsd`*

### `<BitmapFonts>`

- **Children:** `<BitmapFont>`, `<Character>`, `<Word>`
- **Attributes:**
  - `@name` (xs:string) **(required)**
- *Defined in: `bitmapFontsElement.xsd`*

### `<Character>`

- **Type:** `_characterBitmapImportDataType`
- *Defined in: `bitmapFontsElement.xsd`*

### `<Word>`

- **Type:** `_wordBitmapImportDataType`
- *Defined in: `bitmapFontsElement.xsd`*

---

## Clock (AnalogClock/DigitalClock) (11)

### `<AnalogClock>`

> AnalogClock is a container that represents a traditional clock with rotating hands.

- **Children:** `<HourHand>`, `<MinuteHand>`, `<SecondHand>`, `<Localization>`, `<Variant>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@angle` (angleType)
  - `@scaleX` (xs:float)
  - `@scaleY` (xs:float)
  - `@renderMode` (renderModeType)
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/analogClock.xsd`*

### `<DigitalClock>`

> DigitalClock is a container for text-based formatted time.

- **Children:** `<Localization>`, `<Variant>`, `<TimeText>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@angle` (angleType)
  - `@scaleX` (xs:float)
  - `@scaleY` (xs:float)
  - `@renderMode` (renderModeType)
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/digitalClock.xsd`*

### `<Font>`

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@family` (xs:string) **(required)**
  - `@size` (positiveFloatType) **(required)**
  - `@color` (colorAttributeType)
  - `@slant` (inline) `[NORMAL, ITALIC]`
  - `@width` (inline) `[ULTRA_CONDENSED, EXTRA_CONDENSED, CONDENSED, SEMI_CONDENSED, NORMAL, SEMI_EXPANDED, EXPANDED, EXTRA_EXPANDED]`
  - `@weight` (inline) `[THIN, ULTRA_LIGHT, EXTRA_LIGHT, LIGHT, NORMAL, MEDIUM, SEMI_BOLD, BOLD]`
- *Defined in: `clock/timeText.xsd`*

### `<HourHand>`

> A image that represents an hour hand, it rotates 360 degree in 12 hours.

- **Children:** `<Variant>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@resource` (resourcePathType) **(required)**
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/analogClock.xsd`*

### `<Localization>`

> The Localization is used to fix the date or time to a specific locale or timezone when a parent node such as a part or group has an action related to the date or time.

- **Attributes:**
  - `@timeZone` (xs:string)
  - `@locales` (stringListType)
- *Defined in: `clock/analogClock.xsd`*

### `<MinuteHand>`

> A image that represent a minute hand, it rotates 360 degree in 1 hour.

- **Children:** `<Variant>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@resource` (resourcePathType) **(required)**
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/analogClock.xsd`*

### `<SecondHand>`

> A image that represents a second hand, it rotates 360 degree in 1 minute.

- **Children:** `<Variant>`, `<Sweep>`, `<Tick>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@resource` (resourcePathType) **(required)**
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/analogClock.xsd`*

### `<Sweep>`

> Definition of second hand movement. The angle of the second hand will be updated by the given frequency for one second. SYNC_TO_DEVICE means that the angle is updated smoothly as allowed by the device. (Since V2)

- **Attributes:**
  - `@frequency` (inline) **(required)** `[2, 5, 10, 15, SYNC_TO_DEVICE]`
- *Defined in: `clock/secondHand.xsd`*

### `<Tick>`

> Definition of second hand movement. It has 2 attributes below. Strength means intensity that exceeded the final value. 0.5 : has 125% peek value of the final value. 1.0 : has 200% peek value of the final value. Duration means how long the animation is interpolated. 0.2 : 0 ~ 200 (ms) - interpolated 

- **Attributes:**
  - `@strength` (xs:float) **(required)**
  - `@duration` (xs:float) **(required)**
- *Defined in: `clock/secondHand.xsd`*

### `<TimeText>`

> TimeText renders the time within the DigitalClock container.

- **Children:** `<Variant>`, `<BitmapFont>`, `<Font>`
- **Attributes:**
  - `@align` (inline)
  - `@verticalAlign` (inline)
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@family` (xs:string) **(required)**
  - `@size` (positiveFloatType) **(required)**
  - `@color` (colorAttributeType)
  - `@slant` (inline) `[NORMAL, ITALIC]`
  - `@width` (inline) `[ULTRA_CONDENSED, EXTRA_CONDENSED, CONDENSED, SEMI_CONDENSED, NORMAL, SEMI_EXPANDED, EXPANDED, EXTRA_EXPANDED]`
  - `@weight` (inline) `[THIN, ULTRA_LIGHT, EXTRA_LIGHT, LIGHT, NORMAL, MEDIUM, SEMI_BOLD, BOLD]`
  - `@format` (timeFormatType) **(required)**
  - `@hourFormat` (hourFormatType)
  - `@angle` (angleType)
  - `@tintColor` (colorAttributeType)
- *Defined in: `clock/digitalClock.xsd`*

### `<Variant>`

- **Attributes:**
  - `@target` (xs:string) **(required)**
  - `@value` (arithmeticExpressionType) **(required)**
  - `@mode` (inline) **(required)** `[AMBIENT]`
  - `@duration` (inline)
  - `@startOffset` (inline)
  - `@interpolation` (inline) `[LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT, OVERSHOOT, CUBIC_BEZIER]`
  - `@controls` (vector4fType)
  - `@angleDirection` (inline) `[NONE, CLOCKWISE, COUNTER_CLOCKWISE]`
- *Defined in: `clock/analogClock.xsd`*

---

## Common (shared types, transforms, variants) (13)

### `<Animation>`

> Animation for parent element. Use "ANIMATION_VALUE" from the parent element's arithmetic attribute.

- **Attributes:**
  - `@interpolation` (inline) `[LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT, OVERSHOOT, CUBIC_BEZIER]`
  - `@controls` (vector4fType)
  - `@angleDirection` (inline) `[NONE, CLOCKWISE, COUNTER_CLOCKWISE]`
  - `@repeat` (inline)
  - `@fps` (xs:int)
  - `@duration` (nonNegativeFloatType) **(required)**
- *Defined in: `common/animationElement.xsd`*

### `<Compare>`

- **Attributes:**
  - `@expression` (arithmeticExpressionType) **(required)**
- *Defined in: `common/conditionElement.xsd`*

### `<Condition>`

> The Condition element provides the ability to provide a list of options - Compare Elements - each of which is evaluated against an expression, in turn. Only the first successful Compare element is selected, the others are not rendered or enabled. If none of the Compare elements evaluate successfully

- **Children:** `<Expressions>`, `<Compare>`, `<Default>`
- **Attributes:**
  - `@expression` (arithmeticExpressionType) **(required)**
- *Defined in: `common/conditionElement.xsd`*

### `<Default>`

> The Default element is enabled when no Compare element evaluates successfully.

- *Defined in: `common/conditionElement.xsd`*

### `<Expression>`

- **Attributes:**
  - `@name` (xs:string) **(required)**
- *Defined in: `common/expressionsElement.xsd`*

### `<Expressions>`

- **Children:** `<Expression>`
- **Attributes:**
  - `@name` (xs:string) **(required)**
- *Defined in: `common/conditionElement.xsd`*

### `<Group>`

> The Group element contains other groups or parts as children. This is an important node in the scene graph that lays out the components on the scene. The group does not have the ability to draw on its own, but it affects the position, size, angle or color of the child hierarchies.

- **Children:** `<Localization>`, `<Gyro>`, `<Launch>`, `<Transform>`, `<Reference>`, `<Variant>`, `<PartText>`, `<PartImage>`, `<PartAnimatedImage>`, `<PartDraw>`, `<ScreenReader>`, `<Condition>`, `<ListConfiguration>`, `<BooleanConfiguration>`, `<AnalogClock>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@id` (inline)
  - `@name` (inline) **(required)**
  - `@angle` (angleType)
  - `@scaleX` (xs:float)
  - `@scaleY` (xs:float)
  - `@renderMode` (renderModeType)
  - `@tintColor` (colorAttributeType)
  - `@blendMode` (blendModeType)
- *Defined in: `common/conditionElement.xsd`*

### `<Gyro>`

> The Gyro element adjusts some attributes of the parent Group or Part according to an expression using gyro sensor data source. ex. x="(5/90)* clamp([ACCELEROMETER_ANGLE_X], 0, 90) + (-5/-90)* clamp([ACCELEROMETER_ANGLE_X], -90, 0)"

- **Attributes:**
  - `@x` (gyroArithmeticExpressionType)
  - `@y` (gyroArithmeticExpressionType)
  - `@scaleX` (gyroArithmeticExpressionType)
  - `@scaleY` (gyroArithmeticExpressionType)
  - `@angle` (gyroArithmeticExpressionType)
  - `@alpha` (gyroArithmeticExpressionType)
- *Defined in: `common/transform/gyroElements.xsd`*

### `<Launch>`

- **Attributes:**
  - `@target` (launchTargetType) **(required)**
- *Defined in: `common/launchElement.xsd`*

### `<Parameter>`

- **Attributes:**
  - `@expression` (arithmeticExpressionType) **(required)**
- *Defined in: `common/screenReaderElement.xsd`*

### `<Reference>`

> Reference is a new element which can be placed under any scene object supporting Transform. Reference allows you to publish Transformable attributes from a source element, which can be consumed as a DataSource in other expressions within your Scene. The element has three attributes: name, source att

- **Attributes:**
  - `@name` (xs:string) **(required)**
  - `@source` (xs:string) **(required)**
  - `@defaultValue` (_defaultValueType)
- *Defined in: `common/reference/referenceElements.xsd`*

### `<ScreenReader>`

> The user may turn on the talkback screen reader to interact with the watch face with touch and voice feedback. ScreenReader can be attached to any group or part to let user know how they work.

- **Children:** `<Parameter>`
- **Attributes:**
  - `@expression` (arithmeticExpressionType) **(required)**
  - `@stringId` (xs:string) **(required)**
- *Defined in: `common/screenReaderElement.xsd`*

### `<Transform>`

- **Children:** `<Animation>`
- **Attributes:**
  - `@target` (xs:string) **(required)**
  - `@value` (arithmeticExpressionType) **(required)**
  - `@mode` (inline) `[TO, BY]`
- *Defined in: `common/transform/transformElements.xsd`*

---

## Complication (8)

### `<BoundingArc>`

- **Attributes:**
  - `@startAngle` (angleType) **(required)**
  - `@endAngle` (angleType) **(required)**
  - `@centerX` (xs:float) **(required)**
  - `@centerY` (xs:float) **(required)**
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
  - `@thickness` (nonNegativeFloatType) **(required)**
  - `@isRoundEdge` (booleanType)
  - `@outlinePadding` (nonNegativeFloatType)
  - `@direction` (inline) `[CLOCKWISE, COUNTER_CLOCKWISE]`
- *Defined in: `complication/boundingElement.xsd`*

### `<BoundingBox>`

- **Attributes:**
  - `@outlinePadding` (nonNegativeFloatType)
- *Defined in: `complication/boundingElement.xsd`*

### `<BoundingOval>`

- **Attributes:**
  - `@outlinePadding` (nonNegativeFloatType)
- *Defined in: `complication/boundingElement.xsd`*

### `<BoundingRoundBox>`

- **Attributes:**
  - `@cornerRadius` (xs:float)
  - `@outlinePadding` (nonNegativeFloatType)
- *Defined in: `complication/boundingElement.xsd`*

### `<BoundingShape>`

- *Defined in: `complication/boundingElement.xsd`*

### `<Complication>`

- **Children:** `<Group>`, `<Condition>`
- **Attributes:**
  - `@type` (complicationType) **(required)**
- *Defined in: `complication/complicationElement.xsd`*

### `<ComplicationSlot>`

- **Children:** `<DefaultProviderPolicy>`, `<BoundingShape>`, `<Complication>`, `<Variant>`, `<ScreenReader>`
- **Attributes:**
  - `@pivotX` (xs:float)
  - `@pivotY` (xs:float)
  - `@name` (xs:string)
  - `@angle` (angleType)
  - `@scaleX` (xs:float)
  - `@scaleY` (xs:float)
  - `@tintColor` (colorAttributeType)
  - `@slotId` (xs:string) **(required)**
  - `@supportedTypes` (complicationListType) **(required)**
  - `@displayName` (xs:string)
  - `@isCustomizable` (booleanType)
  - `@blendMode` (blendModeType)
- *Defined in: `complication/complicationSlotElement.xsd`*

### `<DefaultProviderPolicy>`

- **Attributes:**
  - `@defaultSystemProvider` (defaultProviderType) **(required)**
  - `@defaultSystemProviderType` (complicationType) **(required)**
  - `@primaryProvider` (xs:string)
  - `@primaryProviderType` (complicationType)
  - `@secondaryProvider` (xs:string)
  - `@secondaryProviderType` (complicationType)
- *Defined in: `complication/complicationSlotElement.xsd`*

---

## Group (6)

### `<BooleanConfiguration>`

- **Children:** `<BooleanOption>`, `<Group>`, `<Condition>`, `<AnalogClock>`, `<DigitalClock>`
- **Attributes:**
  - `@id` (booleanType) **(required)**
- *Defined in: `group/groupElement.xsd`*

### `<ListConfiguration>`

- **Children:** `<ListOption>`, `<Group>`, `<Condition>`, `<AnalogClock>`, `<DigitalClock>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
- *Defined in: `group/groupElement.xsd`*

### `<PartAnimatedImage>`

- **Children:** `<Thumbnail>`, `<AnimationController>`, `<AnimatableImageElement>`
- *Defined in: `group/groupElement.xsd`*

### `<PartDraw>`

> PartDraw is element that draws primitive types of figure like line, rect, arc, circle and rounded rectangle.

- **Children:** `<DrawElement>`
- *Defined in: `group/groupElement.xsd`*

### `<PartImage>`

- **Children:** `<ImageFilters>`, `<ImageElement>`
- *Defined in: `group/groupElement.xsd`*

### `<PartText>`

- **Children:** `<TextElement>`
- *Defined in: `group/groupElement.xsd`*

---

## Group/Part/AnimatedImage (7)

### `<AnimatableImageElement>`

- *Defined in: `group/part/animatedImage/partAnimatedImageElement.xsd`*

### `<AnimatedImage>`

- **Attributes:**
  - `@resource` (resourcePathType) **(required)**
  - `@format` (inline) **(required)** `[IMAGE, AGIF, WEBP]`
  - `@thumbnail` (xs:string)
- *Defined in: `group/part/animatedImage/animatedImageElement.xsd`*

### `<AnimatedImages>`

- **Children:** `<AnimatedImage>`, `<SequenceImages>`
- **Attributes:**
  - `@changeDirection` (directionType)
  - `@change` (eventTriggerListType)
- *Defined in: `group/part/animatedImage/animatedImagesElement.xsd`*

### `<AnimationController>`

- **Attributes:**
  - `@play` (eventTriggerListType) **(required)**
  - `@delayPlay` (nonNegativeFloatType)
  - `@delayRepeat` (nonNegativeFloatType)
  - `@repeat` (booleanType)
  - `@loopCount` (xs:nonNegativeInteger)
  - `@resumePlayBack` (booleanType)
  - `@beforePlaying` (frameOptionType)
  - `@afterPlaying` (frameOptionType)
- *Defined in: `group/part/animatedImage/animationControllerElement.xsd`*

### `<Image>`

> An element for an image.

- **Attributes:**
  - `@resource` (xs:string) **(required)**
- *Defined in: `group/part/animatedImage/sequenceImageElement.xsd`*

### `<SequenceImages>`

- **Children:** `<Image>`
- **Attributes:**
  - `@loopCount` (xs:positiveInteger)
  - `@thumbnail` (xs:string)
  - `@frameRate` (frameRateRangeType)
- *Defined in: `group/part/animatedImage/animatedImagesElement.xsd`*

### `<Thumbnail>`

- **Attributes:**
  - `@resource` (resourcePathType) **(required)**
- *Defined in: `group/part/animatedImage/partAnimatedImageElement.xsd`*

---

## Group/Part/Draw (shapes, gradients, styles) (12)

### `<Arc>`

> Draw arc line with given bound. Center point of arc is the center of the bounds. Angle is given in degrees with 0 indicating 12 o'clock.

- **Children:** `<Stroke>`, `<WeightedStroke>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@startAngle` (angleType) **(required)**
  - `@endAngle` (angleType) **(required)**
  - `@centerX` (xs:float) **(required)**
  - `@centerY` (xs:float) **(required)**
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
  - `@direction` (inline) `[CLOCKWISE, COUNTER_CLOCKWISE]`
- *Defined in: `group/part/draw/shape/arcElement.xsd`*

### `<DrawElement>`

- *Defined in: `group/part/draw/partDrawElement.xsd`*

### `<Ellipse>`

> Draw (fill or stroke) ellipse shape with given bound.

- **Children:** `<Stroke>`, `<Fill>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@x` (xs:float) **(required)**
  - `@y` (xs:float) **(required)**
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
- *Defined in: `group/part/draw/shape/ellipseElement.xsd`*

### `<Fill>`

> Element with an attribute about fill color. It supports gradient colors with a child element, LinearGradient, RadialGradient or SweepGradient. If more than one gradient is added, the gradient added at the last is only valid.

- **Children:** `<LinearGradient>`, `<RadialGradient>`, `<SweepGradient>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@color` (colorAttributeType) **(required)**
- *Defined in: `group/part/draw/shape/ellipseElement.xsd`*

### `<Line>`

> Draw line from start point to end point

- **Children:** `<Stroke>`, `<WeightedStroke>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@startX` (xs:float) **(required)**
  - `@startY` (xs:float) **(required)**
  - `@endX` (xs:float) **(required)**
  - `@endY` (xs:float) **(required)**
- *Defined in: `group/part/draw/shape/lineElement.xsd`*

### `<LinearGradient>`

> Set a gradient color consisting of a progressive transition between two or more colors along a straight line

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@startX` (xs:float) **(required)**
  - `@startY` (xs:float) **(required)**
  - `@endX` (xs:float) **(required)**
  - `@endY` (xs:float) **(required)**
  - `@colors` (colorListType) **(required)**
  - `@positions` (floatListType) **(required)**
- *Defined in: `group/part/draw/gradient/linearGradientElement.xsd`*

### `<RadialGradient>`

> Set a gradient color consisting of a progressive transition between two or more colors that radiate from an origin

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@centerX` (xs:float) **(required)**
  - `@centerY` (xs:float) **(required)**
  - `@radius` (xs:float) **(required)**
  - `@colors` (colorListType) **(required)**
  - `@positions` (floatListType) **(required)**
- *Defined in: `group/part/draw/gradient/radialGradientElement.xsd`*

### `<Rectangle>`

> Draw (fill or stroke) rectangle shape with given bound.

- **Children:** `<Stroke>`, `<Fill>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@x` (xs:float) **(required)**
  - `@y` (xs:float) **(required)**
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
- *Defined in: `group/part/draw/shape/rectangleElement.xsd`*

### `<RoundRectangle>`

> Draw (fill or stroke) rectangle shape that has rounded corners with given bounds.

- **Children:** `<Stroke>`, `<Fill>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@x` (xs:float) **(required)**
  - `@y` (xs:float) **(required)**
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
  - `@cornerRadiusX` (xs:float) **(required)**
  - `@cornerRadiusY` (xs:float) **(required)**
- *Defined in: `group/part/draw/shape/roundRectangleElement.xsd`*

### `<Stroke>`

> Element with attributes for a stroke style. It supports gradient colors with a child element, LinearGradient, RadialGradient or SweepGradient. If more than one gradient is added, the gradient added at the last is only valid.

- **Children:** `<LinearGradient>`, `<RadialGradient>`, `<SweepGradient>`, `<Transform>`, `<Reference>`
- **Attributes:**
  - `@color` (colorAttributeType) **(required)**
  - `@thickness` (nonNegativeFloatType) **(required)**
  - `@dashIntervals` (floatListType)
  - `@dashPhase` (xs:float)
  - `@cap` (inline) `[BUTT, ROUND, SQUARE]`
  - `@join` (inline) `[MITER, ROUND, BEVEL]`
- *Defined in: `group/part/draw/shape/arcElement.xsd`*

### `<SweepGradient>`

> Set a gradient color consisting of a progressive transition between two or more colors that sweep an angle from startAngle to endAngle

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@startAngle` (angleType) **(required)**
  - `@endAngle` (angleType) **(required)**
  - `@centerX` (xs:float) **(required)**
  - `@centerY` (xs:float) **(required)**
  - `@colors` (colorListType) **(required)**
  - `@positions` (floatListType) **(required)**
  - `@direction` (inline) `[CLOCKWISE, COUNTER_CLOCKWISE]`
- *Defined in: `group/part/draw/gradient/sweepGradientElement.xsd`*

### `<WeightedStroke>`

> Stroke style with weight, each element can have different colors.

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@colors` (colorListType) **(required)**
  - `@weights` (colorWeightListType)
  - `@discreteGap` (nonNegativeFloatType)
  - `@interpolate` (interpolateBooleanType)
  - `@thickness` (nonNegativeFloatType) **(required)**
  - `@cap` (inline) `[BUTT, ROUND, SQUARE]`
  - `@join` (inline) `[MITER, ROUND, BEVEL]`
- *Defined in: `group/part/draw/shape/arcElement.xsd`*

---

## Group/Part/Image (5)

### `<HsbFilter>`

> A filter that adjusts pixels by hue, saturate or brightness

- **Attributes:**
  - `@hueRotate` (angleType)
  - `@saturate` (normalizedType)
  - `@brightness` (normalizedType)
- *Defined in: `group/part/image/imageFilter/hsbFilterElement.xsd`*

### `<ImageElement>`

- *Defined in: `group/part/image/partImageElement.xsd`*

### `<ImageFilters>`

> ImageFilters is a container for filters that affect the pixels in the bitmap.

- **Children:** `<HsbFilter>`
- *Defined in: `group/part/image/imageFilter/imageFiltersElement.xsd`*

### `<Images>`

> Images is a container that has a series of image resources. Only one image is shown at a time, and is changed using by tap.

- **Children:** `<Image>`
- **Attributes:**
  - `@change` (eventTriggerListType)
  - `@changeDirection` (directionType)
- *Defined in: `group/part/image/imagesElement.xsd`*

### `<Photos>`

> An element for photos.

- **Attributes:**
  - `@source` (xs:string) **(required)**
  - `@defaultImageResource` (xs:string) **(required)**
  - `@change` (photoEventTriggerListType)
  - `@changeAfterEvery` (inline)
  - `@width` (xs:positiveInteger)
  - `@height` (xs:positiveInteger)
- *Defined in: `group/part/image/photosElement.xsd`*

---

## Group/Part/Text (12)

### `<InlineImage>`

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@resource` (xs:string) **(required)**
  - `@source` (xs:string)
  - `@color` (colorAttributeType)
  - `@overlapLeft` (xs:float)
  - `@overlapRight` (xs:float)
- *Defined in: `group/part/text/formatter/formatterGroup.xsd`*

### `<Lower>`

- **Children:** `<Template>`
- *Defined in: `group/part/text/formatter/formatterGroup.xsd`*

### `<OutGlow>`

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@radius` (xs:float)
  - `@color` (colorAttributeType) **(required)**
- *Defined in: `group/part/text/decoration/decorationGroup.xsd`*

### `<Outline>`

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@width` (positiveFloatType)
  - `@color` (colorAttributeType) **(required)**
- *Defined in: `group/part/text/decoration/decorationGroup.xsd`*

### `<Shadow>`

- **Children:** `<Transform>`, `<Reference>`
- **Attributes:**
  - `@color` (colorAttributeType) **(required)**
  - `@offsetX` (xs:float)
  - `@offsetY` (xs:float)
  - `@radius` (xs:float)
- *Defined in: `group/part/text/decoration/decorationGroup.xsd`*

### `<StrikeThrough>`

- *Defined in: `group/part/text/decoration/abstractDecorationType.xsd`*

### `<Template>`

- **Children:** `<Parameter>`
- *Defined in: `group/part/text/formatter/formatterGroup.xsd`*

### `<Text>`

> Specifies Plain Text configuration for any text

- **Children:** `<Font>`, `<BitmapFont>`
- **Attributes:**
  - `@align` (inline)
  - `@verticalAlign` (inline)
  - `@ellipsis` (booleanType)
  - `@maxLines` (xs:integer)
  - `@lineSpacing` (inline)
  - `@isAutoSize` (booleanType)
- *Defined in: `group/part/text/textElement.xsd`*

### `<TextCircular>`

> Specifies Circular Text configuration

- **Children:** `<Transform>`, `<Reference>`, `<Font>`, `<BitmapFont>`
- **Attributes:**
  - `@startAngle` (angleType) **(required)**
  - `@endAngle` (angleType) **(required)**
  - `@align` (inline)
  - `@verticalAlign` (inline)
  - `@centerX` (xs:float) **(required)**
  - `@centerY` (xs:float) **(required)**
  - `@direction` (circularDirectionType)
  - `@width` (positiveFloatType) **(required)**
  - `@height` (positiveFloatType) **(required)**
  - `@ellipsis` (booleanType)
  - `@isAutoSize` (booleanType)
- *Defined in: `group/part/text/textCircularElement.xsd`*

### `<TextElement>`

- *Defined in: `group/part/text/partTextElement.xsd`*

### `<Underline>`

- *Defined in: `group/part/text/decoration/abstractDecorationType.xsd`*

### `<Upper>`

- **Children:** `<Template>`
- *Defined in: `group/part/text/formatter/formatterGroup.xsd`*

---

## Metadata (1)

### `<Metadata>`

- **Attributes:**
  - `@key` (inline) **(required)**
  - `@value` (inline) **(required)**
- *Defined in: `metadataElement.xsd`*

---

## Root / Other (1)

### `<WatchFace>`

> WatchFace is a root element of watchface.xml. It contains scheme version of the xml specification and the information of the virtual screen used when the sub-elements are created.

- **Children:** `<Metadata>`, `<UserConfigurations>`, `<BitmapFonts>`, `<Scene>`
- **Attributes:**
  - `@width` (xs:positiveInteger) **(required)**
  - `@height` (xs:positiveInteger) **(required)**
  - `@clipShape` (inline) `[NONE, CIRCLE, RECTANGLE]`
  - `@cornerRadiusX` (xs:float)
  - `@cornerRadiusY` (xs:float)
- *Defined in: `watchface.xsd`*

---

## Scene (1)

### `<Scene>`

> Scene is a container of Visual tags. A watch face MUST include at least one Scene.

- **Children:** `<Group>`, `<PartText>`, `<PartImage>`, `<PartAnimatedImage>`, `<PartDraw>`, `<Condition>`, `<ListConfiguration>`, `<BooleanConfiguration>`, `<Variant>`, `<Transform>`, `<Reference>`, `<ComplicationSlot>`, `<AnalogClock>`, `<DigitalClock>`
- **Attributes:**
  - `@backgroundColor` (colorAttributeType)
- *Defined in: `sceneElement.xsd`*

---

## UserConfiguration (9)

### `<BooleanOption>`

- **Children:** `<Group>`, `<Condition>`, `<AnalogClock>`, `<DigitalClock>`
- **Attributes:**
  - `@id` (booleanType) **(required)**
- *Defined in: `userConfiguration/booleanConfigurationElement.xsd`*

### `<ColorConfiguration>`

- **Children:** `<ColorOption>`, `<Group>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
- *Defined in: `userConfiguration/colorConfigurationElement.xsd`*

### `<ColorOption>`

- **Children:** `<Group>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
- *Defined in: `userConfiguration/colorConfigurationElement.xsd`*

### `<Configuration>`

- **Attributes:**
  - `@id` (xs:string) **(required)**
  - `@optionId` (xs:string) **(required)**
  - `@screenReaderText` (xs:string)
- *Defined in: `userConfiguration/flavorElement.xsd`*

### `<Flavor>`

- **Children:** `<Configuration>`, `<ComplicationSlot>`, `<DefaultProviderPolicy>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
  - `@optionId` (xs:string) **(required)**
  - `@screenReaderText` (xs:string)
  - `@slotId` (xs:string) **(required)**
- *Defined in: `userConfiguration/flavorElement.xsd`*

### `<Flavors>`

- **Children:** `<Flavor>`
- *Defined in: `userConfiguration/userConfigurationsElement.xsd`*

### `<ListOption>`

- **Children:** `<Group>`, `<Condition>`, `<AnalogClock>`, `<DigitalClock>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
- *Defined in: `userConfiguration/listConfigurationElement.xsd`*

### `<PhotosConfiguration>`

- **Attributes:**
  - `@id` (xs:string) **(required)**
  - `@displayName` (xs:string)
  - `@icon` (xs:string)
  - `@screenReaderText` (xs:string)
  - `@highlight` (xs:string)
  - `@configType` (inline) **(required)** `[SINGLE, MULTIPLE]`
- *Defined in: `userConfiguration/userConfigurationsElement.xsd`*

### `<UserConfigurations>`

> UserConfigurations is a set of Configuration to support various appearance options. These can be used for Colors, Type of Hands, Background, Complication etc.

- **Children:** `<ListConfiguration>`, `<ListOption>`, `<BooleanConfiguration>`, `<ColorConfiguration>`, `<ColorOption>`, `<Flavors>`, `<Flavor>`, `<PhotosConfiguration>`
- **Attributes:**
  - `@id` (xs:string) **(required)**
  - `@displayName` (xs:string)
  - `@screenReaderText` (xs:string)
  - `@icon` (xs:string)
  - `@childSettingIds` (stringListType)
  - `@complicationSlotIds` (stringListType)
  - `@colors` (userStyleColorOptionType)
  - `@highlight` (xs:string)
  - `@configType` (inline) **(required)** `[SINGLE, MULTIPLE]`
- *Defined in: `userConfiguration/userConfigurationsElement.xsd`*

---

## Enumerations

| Type | Values |
|------|--------|
| `_angleTypeValuePreferences` | `0`, `180`, `360` |
| `_anyExpressionType` | `[`, `]` |
| `_colorValuePreferences` | `0`, `128`, `255` |
| `_functionType` | `round()`, `floor()`, `ceil()`, `fract()`, `sin()`, `cos()`, `tan()`, `asin()`, `acos()`, `atan()`, `abs()`, `clamp(,,)`, `rand(,)`, `log()`, `log2()`, `log10()`, `sqrt()`, `cbrt()`, `exp()`, `expm1()` |
| `_normalizedValuePreferences` | `0.0`, `0.5`, `1.0` |
| `_operatorType` | `+`, `-`, `*`, `/`, `%`, `~`, `!`, `|`, `||`, `&`, `&&`, `(`, `)`, `>`, `>=`, `?`, `:`, `==` |
| `_predefinedMetadataKeys` | `PREVIEW_TIME`, `CLOCK_TYPE`, `STEP_GOAL` |
| `_predefinedMetadataValues` | `DIGITAL`, `ANALOG` |
| `_systemShortcutType` | `ALARM`, `BATTERY_STATUS`, `CALENDAR`, `MESSAGE`, `MUSIC_PLAYER`, `PHONE`, `SETTINGS`, `HEALTH_HEART_RATE` |
| `_timeSourceType` | `UTC_TIMESTAMP`, `SECOND_MILLISECOND`, `SECONDS_IN_DAY`, `SECONDS_SINCE_EPOCH`, `MINUTE_SECOND`, `MINUTES_SINCE_EPOCH`, `HOUR_0_11`, `HOUR_0_11_Z`, `HOUR_0_11_MINUTE`, `HOUR_1_12`, `HOUR_1_12_Z`, `HOUR_1_12_MINUTE`, `HOUR_0_23`, `HOUR_0_23_Z`, `HOUR_0_23_MINUTE`, `HOUR_1_24`, `HOUR_1_24_Z`, `HOUR_1_24_MINUTE`, `HOURS_SINCE_EPOCH`, `DAY_HOUR` |
| `_weatherSourceEnums` | `WEATHER.IS_AVAILABLE`, `WEATHER.IS_ERROR`, `WEATHER.CONDITION`, `WEATHER.CONDITION_NAME`, `WEATHER.IS_DAY`, `WEATHER.TEMPERATURE`, `WEATHER.TEMPERATURE_UNIT`, `WEATHER.TEMPERATURE_LOW`, `WEATHER.TEMPERATURE_HIGH`, `WEATHER.CHANCE_OF_PRECIPITATION`, `WEATHER.UV_INDEX`, `WEATHER.LAST_UPDATED` |
| `batterySourceType` | `BATTERY_PERCENT`, `BATTERY_CHARGING_STATUS`, `BATTERY_IS_LOW`, `BATTERY_TEMPERATURE_CELSIUS`, `BATTERY_TEMPERATURE_FAHRENHEIT` |
| `blendModeType` | `CLEAR`, `COLOR`, `COLOR_BURN`, `COLOR_DODGE`, `DARKEN`, `DIFFERENCE`, `DST`, `DST_ATOP`, `DST_IN`, `DST_OUT`, `DST_OVER`, `EXCLUSION`, `HARD_LIGHT`, `HUE`, `LIGHTEN`, `LUMINOSITY`, `MODULATE`, `MULTIPLY`, `OVERLAY`, `PLUS` |
| `booleanType` | `TRUE`, `FALSE` |
| `circularDirectionType` | `CLOCKWISE`, `COUNTER_CLOCKWISE` |
| `complicationType` | `SHORT_TEXT`, `LONG_TEXT`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`, `PHOTO_IMAGE`, `RANGED_VALUE`, `GOAL_PROGRESS`, `WEIGHTED_ELEMENTS`, `EMPTY` |
| `defaultProviderType` | `APP_SHORTCUT`, `DATE`, `DAY_OF_WEEK`, `FAVORITE_CONTACT`, `NEXT_EVENT`, `STEP_COUNT`, `SUNRISE_SUNSET`, `TIME_AND_DATE`, `UNREAD_NOTIFICATION_COUNT`, `WATCH_BATTERY`, `WORLD_CLOCK`, `DAY_AND_DATE`, `EMPTY`, `HEART_RATE` |
| `directionType` | `FORWARD`, `BACKWARD`, `RANDOM` |
| `eventTriggerType` | `TAP`, `ON_VISIBLE`, `ON_NEXT_SECOND`, `ON_NEXT_MINUTE`, `ON_NEXT_HOUR` |
| `frameOptionType` | `DO_NOTHING`, `FIRST_FRAME`, `THUMBNAIL`, `HIDE` |
| `healthSourceType` | `STEP_COUNT`, `STEP_GOAL`, `STEP_PERCENT`, `HEART_RATE`, `HEART_RATE_Z` |
| `hourFormatType` | `12`, `24`, `SYNC_TO_DEVICE` |
| `languageSourceType` | `LANGUAGE_CODE`, `LANGUAGE_COUNTRY_CODE`, `LANGUAGE_LOCALE_NAME`, `LANGUAGE_TEXT_DIRECTION` |
| `moonPhaseSourceType` | `MOON_PHASE_POSITION`, `MOON_PHASE_TYPE`, `MOON_PHASE_TYPE_STRING` |
| `notificationSourceType` | `UNREAD_NOTIFICATION_COUNT` |
| `photoEventTriggerType` | `TAP`, `ON_VISIBLE` |
| `renderModeType` | `SOURCE`, `MASK`, `ALL` |
| `sensorSourceType` | `ACCELEROMETER_IS_SUPPORTED`, `ACCELEROMETER_X`, `ACCELEROMETER_Y`, `ACCELEROMETER_Z`, `ACCELEROMETER_ANGLE_X`, `ACCELEROMETER_ANGLE_Y`, `ACCELEROMETER_ANGLE_Z`, `ACCELEROMETER_ANGLE_XY` |
| `timeUnitSourceType` | `MILLISECOND`, `SECOND`, `SECOND_Z`, `MINUTE`, `MINUTE_Z`, `AMPM_STATE`, `DAY`, `DAY_Z`, `MONTH`, `MONTH_Z`, `MONTH_F`, `MONTH_S`, `YEAR`, `YEAR_S` |
