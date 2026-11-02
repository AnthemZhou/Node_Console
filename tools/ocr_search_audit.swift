// Read native popup screenshots using macOS Vision; no ranking logic here.
import Foundation
import Vision
import ImageIO
import UniformTypeIdentifiers

let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let report = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("report.json"))) as! [String: Any]
let samples = report["samples"] as! [[String: Any]]
var output: [[String: Any]] = []
for sample in samples {
    let filename = sample["screenshot"] as! String
    let source = CGImageSourceCreateWithURL(root.appendingPathComponent(filename) as CFURL, nil)!
    let image = CGImageSourceCreateImageAtIndex(source, 0, nil)!
    let mouse = sample["mouse"] as! [Int]
    // Blender area/event coordinates are framebuffer pixels, unlike window.width.
    let rect = CGRect(x: max(0, Double(mouse[0]) - 50),
                      y: max(0, Double(image.height) - Double(mouse[1]) - 70),
                      width: min(1250, Double(image.width) - Double(mouse[0]) + 50),
                      height: 650)
    let cropped = image.cropping(to: rect)!
    var pixels = [UInt8](repeating: 0, count: cropped.width * cropped.height * 4)
    pixels.withUnsafeMutableBytes { buffer in
        let context = CGContext(data: buffer.baseAddress, width: cropped.width, height: cropped.height,
                                bitsPerComponent: 8, bytesPerRow: cropped.width * 4,
                                space: CGColorSpaceCreateDeviceRGB(),
                                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
        context.draw(cropped, in: CGRect(x: 0, y: 0, width: cropped.width, height: cropped.height))
    }
    let ink = (0..<10).map { row -> Int in
        var count = 0
        for y in (144 + row * 40)..<(169 + row * 40) {
            for x in 55..<min(1000, cropped.width) {
                let offset = (y * cropped.width + x) * 4
                if max(pixels[offset], pixels[offset + 1], pixels[offset + 2]) > 110 { count += 1 }
            }
        }
        return count
    }
    let target = root.appendingPathComponent("crop-" + filename)
    let destination = CGImageDestinationCreateWithURL(target as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(destination, cropped, nil)
    CGImageDestinationFinalize(destination)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    let locales = ["zh_HANS": "zh-Hans", "ja_JP": "ja-JP", "ko_KR": "ko-KR", "ru_RU": "ru-RU", "es": "es-ES"]
    let supported = try request.supportedRecognitionLanguages()
    let locale = locales[sample["language"] as? String ?? ""]
    request.recognitionLanguages = locale.map { supported.contains($0) ? [$0, "en-US"] : ["en-US"] } ?? ["en-US"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: cropped).perform([request])
    let lines = (request.results ?? []).map { observation -> [String: Any] in
        let box = observation.boundingBox
        return ["box": [box.minX, box.minY, box.width, box.height],
                "text": observation.topCandidates(1).first?.string ?? "",
                "confidence": observation.topCandidates(1).first?.confidence ?? 0]
    }
    output.append(["index": sample["index"]!, "lines": lines, "ink": ink,
                   "rect": [rect.minX, rect.minY, rect.width, rect.height]])
    if output.count % 20 == 0 { print("OCR_PROGRESS \(output.count)") }
}
let data = try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys])
try data.write(to: root.appendingPathComponent("ocr.json"))
print("OCR_COMPLETE \(output.count)")
