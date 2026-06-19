# test_edge_tts_ssml.py
import asyncio
import edge_tts

async def test_edge_tts_ssml():
    voice = "zh-CN-YunxiNeural"
    
    print("=" * 60)
    print("Edge TTS SSML 功能测试")
    print("=" * 60)
    
    # ============================================
    # 测试1：纯文本（对照组，应该正常）
    # ============================================
    print("\n[测试1] 纯文本（对照组）")
    text1 = "这是一个正常的语音合成测试"
    await edge_tts.Communicate(text1, voice).save("test1_plain.mp3")
    print("  已生成: test1_plain.mp3（应朗读纯文本）")
    
    # ============================================
    # 测试2：简单 SSML（只带 speak 和 voice）
    # ============================================
    print("\n[测试2] 简单 SSML")
    ssml2 = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
        <voice name="{voice}">
            这是简单的 SSML 测试
        </voice>
    </speak>
    """
    await edge_tts.Communicate(ssml2, voice).save("test2_simple_ssml.mp3")
    print("  已生成: test2_simple_ssml.mp3")
    
    # ============================================
    # 测试3：带 prosody（语速变化）
    # ============================================
    print("\n[测试3] 带 prosody 标签")
    ssml3 = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
        <voice name="{voice}">
            <prosody rate="+50%" pitch="+10%">
                这是语速加快的语音
            </prosody>
            <break time="500ms"/>
            <prosody rate="-20%" pitch="-10%">
                这是语速放慢的语音
            </prosody>
        </voice>
    </speak>
    """
    await edge_tts.Communicate(ssml3, voice).save("test3_prosody.mp3")
    print("  已生成: test3_prosody.mp3")
    
    # ============================================
    # 测试4：不带 speak 和 voice（只有 prosody）
    # ============================================
    print("\n[测试4] 只有 prosody（不完整格式）")
    ssml4 = f"""
    <prosody rate="+20%" pitch="+5%">
        这是只有 prosody 没有 speak 的测试
    </prosody>
    """
    try:
        await edge_tts.Communicate(ssml4, voice).save("test4_only_prosody.mp3")
        print("  已生成: test4_only_prosody.mp3")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # ============================================
    # 测试5：有 speak 但没有 voice
    # ============================================
    print("\n[测试5] 有 speak 但没有 voice")
    ssml5 = f"""
    <speak version="1.0">
        <prosody rate="+20%" pitch="+5%">
            这是没有 voice 标签的测试
        </prosody>
    </speak>
    """
    try:
        await edge_tts.Communicate(ssml5, voice).save("test5_no_voice.mp3")
        print("  已生成: test5_no_voice.mp3")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # ============================================
    # 测试6：你的脚本实际输出的格式（片段）
    # ============================================
    print("\n[测试6] 模拟你的脚本输出（片段）")
    ssml6 = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
        <voice name="zh-CN-YunxiNeural">
            <prosody rate="-15%" pitch="0%">暮色中的街巷静谧如画</prosody><break time="300ms"/>
        </voice>
    </speak>
    """
    await edge_tts.Communicate(ssml6, voice).save("test6_your_format.mp3")
    print("  已生成: test6_your_format.mp3")
    
    # ============================================
    # 测试7：纯文本 + SSML 混合（可能朗读标签）
    # ============================================
    print("\n[测试7] 混合内容（可能朗读标签）")
    ssml7 = f"""
    <speak>
        <voice name="{voice}">
            这是正常内容
            <prosody rate="+10%">这是加速内容</prosody>
            这是正常内容
        </voice>
    </speak>
    """
    await edge_tts.Communicate(ssml7, voice).save("test7_mixed.mp3")
    print("  已生成: test7_mixed.mp3")
    
    print("\n" + "=" * 60)
    print("测试完成！请播放生成的 MP3 文件，检查效果")
    print("=" * 60)
    print("\n文件列表：")
    print("  1. test1_plain.mp3       - 纯文本（对照组）")
    print("  2. test2_simple_ssml.mp3 - 简单 SSML")
    print("  3. test3_prosody.mp3     - 带 prosody（语速变化）")
    print("  4. test4_only_prosody.mp3 - 只有 prosody（可能失败）")
    print("  5. test5_no_voice.mp3    - 没有 voice（可能失败）")
    print("  6. test6_your_format.mp3 - 模拟你的脚本格式")
    print("  7. test7_mixed.mp3       - 混合内容")
    print("\n建议对比 test1_plain.mp3 和 test6_your_format.mp3")
    print("如果 test6 没有朗读标签，说明 SSML 格式正确；")
    print("如果 test6 朗读了标签，说明 Edge TTS 不支持该格式。")

if __name__ == "__main__":
    asyncio.run(test_edge_tts_ssml())