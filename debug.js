// 前端调试工具脚本
console.log('🔧 前端调试工具已加载');

// 检查必需的库是否存在
const checkLibraries = () => {
    const results = {
        Vue: typeof Vue !== 'undefined',
        ElementPlus: typeof ElementPlus !== 'undefined', 
        ElementPlusIconsVue: typeof ElementPlusIconsVue !== 'undefined'
    };
    
    console.log('📚 库检查结果:', results);
    
    Object.entries(results).forEach(([name, exists]) => {
        if (!exists) {
            console.error(`❌ ${name} 库未加载`);
        } else {
            console.log(`✅ ${name} 库已加载`);
        }
    });
    
    return Object.values(results).every(Boolean);
};

// 检查Vue应用挂载状态
const checkVueApp = () => {
    const appElement = document.getElementById('app');
    if (!appElement) {
        console.error('❌ 未找到#app元素');
        return false;
    }
    
    if (appElement.__vue_app__) {
        console.log('✅ Vue应用已挂载');
        return true;
    } else {
        console.warn('⚠️ Vue应用尚未挂载');
        return false;
    }
};

// 监听DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM加载完成，开始检查...');
    
    setTimeout(() => {
        checkLibraries();
        checkVueApp();
    }, 1000);
});

// 监听错误
window.addEventListener('error', (event) => {
    console.error('💥 JavaScript错误:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('💥 未处理的Promise拒绝:', event.reason);
});