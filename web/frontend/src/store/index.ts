import { createStore } from 'vuex'
import globals from './modules/globals'
import captures from './modules/captures'

export default createStore({
    modules: {
        globals,
        captures
    }
})
