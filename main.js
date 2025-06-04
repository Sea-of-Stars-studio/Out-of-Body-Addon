//@ts-ignore
import { world, system, EasingType } from "@minecraft/server";

// 帮助信息
const HELP_MESSAGE = `§e====== 灵魂出窍模式帮助 ======
§a开启 §f-  开启灵魂出窍模式
§c关闭 §f-  关闭灵魂出窍模式
§b帮助 §f-  显示此帮助信息
§6信息 §f-  模组目前正在稳定更新
         版本号：E1.0.0-alpha.1
         作者：EnderTrekker
         工作室：星之海工作室
§e============================`;
world.afterEvents.playerSpawn.subscribe((event) => {
    if (event.initialSpawn) { // 只在首次生成时显示
        system.runTimeout(() => {
            event.player.sendMessage(HELP_MESSAGE);
        }, 20); // 延迟1秒显示，确保玩家完全加载
    }
});
//@ts-ignore
world.beforeEvents.chatSend.subscribe((event) => {
    // 获取运行ID并确保是数字类型
    var freeCameraRunId = Number(event.sender.getDynamicProperty("freeCameraRunId")) || 0;
    
    // 显示帮助信息
    if (event.message === "帮助") {
        event.cancel = true;
        event.sender.sendMessage(HELP_MESSAGE);
        return;
    }
    
    // 关闭灵魂出窍模式
    if (freeCameraRunId !== 0 && event.message === "关闭") {
        event.cancel = true;
        system.clearRun(freeCameraRunId);
        event.sender.setDynamicProperty("freeCameraRunId", 0);
        system.run(() => {
            event.sender.camera.clear();
            event.sender.sendMessage("§c灵魂出窍模式已关闭");
        });
        return;
    }
    
    // 开启灵魂出窍模式
    if (freeCameraRunId === 0 && event.message.startsWith("开启")) {
        event.cancel = true;
        system.run(() => {
            var originLocation = event.sender.location;
            var speed = 7; // 固定速度设为7
            var cameraX = originLocation.x;
            var cameraY = originLocation.y;
            var cameraZ = originLocation.z;
            
            event.sender.sendMessage("§a灵魂出窍模式已开启");
            
            const runId = system.runInterval(() => {
                // 确保所有坐标都是数字
                cameraX = Number(cameraX) + (Number(event.sender.location.x) - Number(originLocation.x)) * speed;
                if (event.sender.isSneaking) {
                    cameraY = Number(cameraY) - 3;
                }
                if (event.sender.isJumping) {
                    cameraY = Number(cameraY) + 3;
                }
                cameraZ = Number(cameraZ) + (Number(event.sender.location.z) - Number(originLocation.z)) * speed;
                
                // 计算相机与玩家的距离
                const dx = Number(cameraX) - Number(originLocation.x);
                const dy = Number(cameraY) - Number(originLocation.y);
                const dz = Number(cameraZ) - Number(originLocation.z);
                const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
                
                // 如果距离超过100格，自动关闭
                if (distance > 100) {
                    system.clearRun(runId);
                    event.sender.setDynamicProperty("freeCameraRunId", 0);
                    event.sender.camera.clear();
                    event.sender.sendMessage("§c灵魂出窍模式已关闭");
                    return;
                }
                
                try {
                    event.sender.camera.setCamera("minecraft:free", { 
                        easeOptions: { easeTime: 0.25, easeType: EasingType.Linear }, 
                        location: { 
                            x: Number(cameraX), 
                            y: Number(cameraY), 
                            z: Number(cameraZ) 
                        }, 
                        rotation: event.sender.getRotation() 
                    });
                }
                catch (e) { 
                    console.warn("Camera error:", e);
                }
                event.sender.teleport(originLocation, { rotation: event.sender.getRotation() });
            }, 5);
            
            // 确保存储为数字
            event.sender.setDynamicProperty("freeCameraRunId", Number(runId));
        });
        return;
    }
});

// 其他事件监听器也需要确保类型正确
world.afterEvents.entityHurt.subscribe((event) => {
    const freeCameraRunId = Number(event.hurtEntity.getDynamicProperty("freeCameraRunId")) || 0;
    if (freeCameraRunId !== 0) {
        system.clearRun(freeCameraRunId);
        event.hurtEntity.setDynamicProperty("freeCameraRunId", 0);
        system.run(() => {
            event.hurtEntity.camera.clear();
            event.hurtEntity.sendMessage("§c灵魂出窍模式已关闭");
        });
    }
}, { entityTypes: ["minecraft:player"] });

world.afterEvents.playerDimensionChange.subscribe((event) => {
    const freeCameraRunId = Number(event.player.getDynamicProperty("freeCameraRunId")) || 0;
    if (freeCameraRunId !== 0) {
        system.clearRun(freeCameraRunId);
        event.player.setDynamicProperty("freeCameraRunId", 0);
        system.run(() => {
            event.player.camera.clear();
            event.player.sendMessage("§c灵魂出窍模式已关闭");
        });
    }
});

world.afterEvents.entityDie.subscribe((event) => {
    const freeCameraRunId = Number(event.deadEntity.getDynamicProperty("freeCameraRunId")) || 0;
    if (freeCameraRunId !== 0) {
        system.clearRun(freeCameraRunId);
        event.deadEntity.setDynamicProperty("freeCameraRunId", 0);
        system.run(() => {
            event.deadEntity.camera.clear();
            event.deadEntity.sendMessage("§c灵魂出窍模式已关闭");
        });
    }
}, { entityTypes: ["minecraft:player"] });

world.beforeEvents.playerLeave.subscribe((event) => {
    const freeCameraRunId = Number(event.player.getDynamicProperty("freeCameraRunId")) || 0;
    if (freeCameraRunId !== 0) {
        system.clearRun(freeCameraRunId);
        event.player.setDynamicProperty("freeCameraRunId", 0);
    }
});